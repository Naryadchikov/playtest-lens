import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyzer import client

FIXTURE = Path(__file__).parent / "fixtures" / "cached_reply.json"
PROMPT = "find moments"


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


class ExplodingFiles:
    def create(self, **kwargs):
        raise AssertionError("network call attempted")


class ExplodingResponses:
    def create(self, **kwargs):
        raise AssertionError("network call attempted")


class FakeFiles:
    def __init__(self, ids=None):
        self.calls = 0
        self._ids = list(ids) if ids else ["file_123"]

    def create(self, file=None, purpose=None):
        self.calls += 1
        file_id = self._ids.pop(0) if len(self._ids) > 1 else self._ids[0]
        return SimpleNamespace(id=file_id)


class FakeResponses:
    def __init__(self, payload=None):
        self.calls = 0
        self._payload = payload or {
            "id": "resp_1",
            "model": "muse-spark-1.3",
            "output_text": "[]",
            "usage": {"input_tokens": 1_000_000, "output_tokens": 1_000_000},
        }

    def create(self, model=None, input=None):
        self.calls += 1
        return FakeResponse(self._payload)


def _video(tmp_path, name="clip.mp4", content=b"video-bytes"):
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_cached_reply_returned_without_network(tmp_path):
    video = _video(tmp_path)
    cache_dir = tmp_path / "cache"
    costs = tmp_path / "costs.jsonl"
    cached = json.loads(FIXTURE.read_text())
    seeding = SimpleNamespace(files=FakeFiles(), responses=FakeResponses(payload=cached))
    first = client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=video,
        purpose="test", cache_dir=cache_dir, costs_path=costs, client=seeding,
    )
    assert first == cached
    assert len(costs.read_text().strip().splitlines()) == 1

    exploding = SimpleNamespace(files=ExplodingFiles(), responses=ExplodingResponses())
    reply = client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=video,
        purpose="test", cache_dir=cache_dir, costs_path=costs, client=exploding,
    )
    assert reply == cached
    assert len(costs.read_text().strip().splitlines()) == 1


def test_same_content_under_two_file_ids_is_cache_hit(tmp_path):
    first_video = _video(tmp_path, name="a.mp4")
    second_video = _video(tmp_path, name="b.mp4")
    cache_dir = tmp_path / "cache"
    costs = tmp_path / "costs.jsonl"
    # Each upload would return a different id; the second call must not need it.
    fake = SimpleNamespace(
        files=FakeFiles(ids=["file_aaa", "file_bbb"]), responses=FakeResponses()
    )
    client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=first_video,
        purpose="test", cache_dir=cache_dir, costs_path=costs, client=fake,
    )
    assert fake.files.calls == 1
    assert fake.responses.calls == 1
    client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=second_video,
        purpose="test", cache_dir=cache_dir, costs_path=costs, client=fake,
    )
    assert fake.responses.calls == 1
    assert fake.files.calls == 1
    assert len(costs.read_text().strip().splitlines()) == 1


def test_real_call_adds_one_cost_line(tmp_path):
    video = _video(tmp_path)
    cache_dir = tmp_path / "cache"
    costs = tmp_path / "costs.jsonl"
    fake = SimpleNamespace(files=FakeFiles(), responses=FakeResponses())
    client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=video,
        purpose="spark_test:clip.mp4", cache_dir=cache_dir, costs_path=costs, client=fake,
    )
    assert fake.responses.calls == 1
    lines = costs.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["model"] == "muse-spark-1.3"
    assert entry["input_tokens"] == 1_000_000
    assert entry["output_tokens"] == 1_000_000
    assert entry["cost_usd"] == pytest.approx(5.50)
    assert entry["purpose"] == "spark_test:clip.mp4"
    assert "time" in entry
    client.call_model(
        model="muse-spark-1.3", prompt=PROMPT, video_path=video,
        purpose="spark_test:clip.mp4", cache_dir=cache_dir, costs_path=costs, client=fake,
    )
    assert fake.responses.calls == 1
    assert len(costs.read_text().strip().splitlines()) == 1


def test_upload_remembered_by_content_hash(tmp_path):
    video = _video(tmp_path)
    fake_files = FakeFiles()
    fake = SimpleNamespace(files=fake_files, responses=FakeResponses())
    first = client.upload_file(video, client=fake, cache_dir=tmp_path / "cache")
    second = client.upload_file(video, client=fake, cache_dir=tmp_path / "cache")
    assert first == second == "file_123"
    assert fake_files.calls == 1
