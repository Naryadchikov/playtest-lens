import json
import subprocess
from types import SimpleNamespace

import pytest

from analyzer import client
from tools.video import sample_frames

OPEN_MODEL = "meta-models/muse-spark-open-1026"
PROMPT = "check this clip"
VERDICT = {
    "verdict": "keep",
    "kind": "stuck",
    "friction": "stuck",
    "resolved": "unknown",
    "note": "The player retries the same jump.",
    "summary": "The player could not clear the gap.",
    "quote": None,
    "game_state": None,
    "puzzle": "Vent",
    "area": "Hall",
}
CHAT_PAYLOAD = {
    "id": "chat_1",
    "model": OPEN_MODEL,
    "choices": [
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "<|start|>assistant\n" + json.dumps(VERDICT),
                "reasoning_content": "private notes",
            },
        }
    ],
    "usage": {"prompt_tokens": 1000, "completion_tokens": 2000},
}


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


class FakeCompletions:
    def __init__(self, payload=None):
        self.calls = []
        self.payload = payload or CHAT_PAYLOAD

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.payload)


class ExplodingCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        raise AssertionError("network call attempted")


class FakeOpenClient:
    def __init__(self, completions=None):
        self.completions = completions or FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.fixture
def frames(tmp_path, monkeypatch):
    paths = []
    for index, data in enumerate((b"jpeg-one", b"jpeg-two"), start=1):
        path = tmp_path / f"frame-{index:03d}.jpg"
        path.write_bytes(data)
        paths.append(path)
    monkeypatch.setattr(client, "sample_frames", lambda *args, **kwargs: list(paths))
    return paths


def _video(tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"video-bytes")
    return path


def _call(tmp_path, fake, *, prompt=PROMPT, video=None):
    return client.call_model(
        model=OPEN_MODEL,
        prompt=prompt,
        video_path=video or _video(tmp_path),
        purpose="check:talos.mp4",
        cache_dir=tmp_path / "cache",
        costs_path=tmp_path / "costs.jsonl",
        client=fake,
    )


def test_open_model_routes_to_baseten_chat_and_strips_marker(tmp_path, frames):
    fake = FakeOpenClient()
    reply = _call(tmp_path, fake)
    assert len(fake.completions.calls) == 1
    assert client.extract_text(reply) == json.dumps(VERDICT)


def test_open_request_shape(tmp_path, frames):
    fake = FakeOpenClient()
    _call(tmp_path, fake)
    request = fake.completions.calls[0]
    assert request["model"] == OPEN_MODEL
    assert request["max_tokens"] >= 1500
    assert len(request["messages"]) == 1
    message = request["messages"][0]
    assert message["role"] == "user"
    content = message["content"]
    images = [part for part in content if part.get("type") == "image_url"]
    texts = [part for part in content if part.get("type") == "text"]
    assert len(images) == len(frames)
    assert all(
        part["image_url"]["url"].startswith("data:image/jpeg;base64,") for part in images
    )
    assert texts == [{"type": "text", "text": PROMPT}]
    assert not any(part.get("type") == "input_audio" for part in content)


def test_open_reply_feeds_extract_text_and_usage(tmp_path, frames):
    reply = _call(tmp_path, FakeOpenClient())
    assert reply["output_text"] == json.dumps(VERDICT)
    assert reply["finish_reason"] == "stop"
    assert "private notes" not in json.dumps(reply)
    input_tokens, output_tokens, cost = client.usage_and_cost(OPEN_MODEL, reply)
    assert (input_tokens, output_tokens) == (1000, 2000)
    assert cost == pytest.approx(0.00975)


def test_open_reply_is_cached_with_no_second_call(tmp_path, frames):
    first = _call(tmp_path, FakeOpenClient())
    exploding = FakeOpenClient(completions=ExplodingCompletions())
    second = _call(tmp_path, exploding)
    assert second == first
    assert len(exploding.completions.calls) == 0
    assert len((tmp_path / "costs.jsonl").read_text().strip().splitlines()) == 1


def test_one_cost_line_per_real_call(tmp_path, frames):
    _call(tmp_path, FakeOpenClient())
    lines = (tmp_path / "costs.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["model"] == OPEN_MODEL
    assert entry["input_tokens"] == 1000
    assert entry["output_tokens"] == 2000
    assert entry["cost_usd"] == pytest.approx(0.00975)
    assert entry["purpose"] == "check:talos.mp4"
    assert "time" in entry


def test_missing_baseten_key_stops_before_any_call(tmp_path, frames, monkeypatch, capsys):
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        _call(tmp_path, None)
    assert excinfo.value.code == 1
    assert "BASETEN_API_KEY is not set" in capsys.readouterr().err


def _jpeg_size(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.strip()[-400:]
    stream = json.loads(result.stdout)["streams"][0]
    return stream["width"], stream["height"]


def test_sample_frames_count_and_long_side(tmp_path):
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=1920x1080:rate=5:duration=6",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
    )
    frames = sample_frames(source, tmp_path / "frames")
    # 6 s at one frame per 2 s, inside the 8 frame cap.
    assert len(frames) == 3
    width, height = _jpeg_size(frames[0])
    assert max(width, height) == 768
    assert frames[0].read_bytes().startswith(b"\xff\xd8")


def test_sample_frames_caps_a_long_clip_at_eight(tmp_path):
    source = tmp_path / "long.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x240:rate=5:duration=20",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
    )
    frames = sample_frames(source, tmp_path / "frames")
    # 20 s at 2 s spacing would be 10 frames; Baseten takes at most 8.
    assert len(frames) == 8
    width, height = _jpeg_size(frames[0])
    assert (width, height) == (320, 240)


def test_open_reply_without_answer_text_fails_and_is_not_cached(tmp_path, frames):
    empty = json.loads(json.dumps(CHAT_PAYLOAD))
    empty["choices"][0]["message"]["content"] = ""
    empty["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError, match="no answer text"):
        _call(tmp_path, FakeOpenClient(FakeCompletions(empty)))
    assert not list((tmp_path / "cache").glob("*.json"))
    assert len((tmp_path / "costs.jsonl").read_text().splitlines()) == 1
