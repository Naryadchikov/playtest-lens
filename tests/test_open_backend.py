import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyzer import client

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


# A fake extract_audio that writes the wav bytes held in the returned box.
@pytest.fixture
def wav(monkeypatch):
    box = {"bytes": b"wav-bytes"}

    def fake_extract_audio(video, output_path, *args, **kwargs):
        Path(output_path).write_bytes(box["bytes"])
        return Path(output_path)

    monkeypatch.setattr(client, "extract_audio", fake_extract_audio)
    return box


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


def test_open_model_routes_to_baseten_chat_and_strips_marker(tmp_path, wav):
    fake = FakeOpenClient()
    reply = _call(tmp_path, fake)
    assert len(fake.completions.calls) == 1
    assert client.extract_text(reply) == json.dumps(VERDICT)


def test_open_request_shape(tmp_path, wav):
    fake = FakeOpenClient()
    _call(tmp_path, fake)
    request = fake.completions.calls[0]
    assert request["model"] == OPEN_MODEL
    assert request["max_tokens"] >= 1500
    assert len(request["messages"]) == 1
    message = request["messages"][0]
    assert message["role"] == "user"
    content = message["content"]
    assert [part["type"] for part in content] == ["video_url", "input_audio", "text"]
    video_url = content[0]["video_url"]["url"]
    prefix = "data:video/mp4;base64,"
    assert video_url.startswith(prefix)
    assert base64.b64decode(video_url[len(prefix):]) == b"video-bytes"
    audio = content[1]["input_audio"]
    assert base64.b64decode(audio["data"]) == b"wav-bytes"
    assert audio["format"] == "wav"
    assert content[2] == {"type": "text", "text": PROMPT}

def test_different_wav_bytes_are_a_cache_miss(tmp_path, wav):
    first = FakeOpenClient()
    _call(tmp_path, first)
    wav["bytes"] = b"other-wav-bytes"
    second = FakeOpenClient()
    _call(tmp_path, second)
    assert len(first.completions.calls) == 1
    assert len(second.completions.calls) == 1
    assert len((tmp_path / "costs.jsonl").read_text().strip().splitlines()) == 2


def test_open_reply_feeds_extract_text_and_usage(tmp_path, wav):
    reply = _call(tmp_path, FakeOpenClient())
    assert reply["output_text"] == json.dumps(VERDICT)
    assert reply["finish_reason"] == "stop"
    assert "private notes" not in json.dumps(reply)
    input_tokens, output_tokens, cost = client.usage_and_cost(OPEN_MODEL, reply)
    assert (input_tokens, output_tokens) == (1000, 2000)
    assert cost == pytest.approx(0.00975)


def test_open_reply_is_cached_with_no_second_call(tmp_path, wav):
    first = _call(tmp_path, FakeOpenClient())
    exploding = FakeOpenClient(completions=ExplodingCompletions())
    second = _call(tmp_path, exploding)
    assert second == first
    assert len(exploding.completions.calls) == 0
    assert len((tmp_path / "costs.jsonl").read_text().strip().splitlines()) == 1


def test_one_cost_line_per_real_call(tmp_path, wav):
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


def test_missing_baseten_key_stops_before_any_call(tmp_path, wav, monkeypatch, capsys):
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        _call(tmp_path, None)
    assert excinfo.value.code == 1
    assert "BASETEN_API_KEY is not set" in capsys.readouterr().err


def test_open_reply_without_answer_text_fails_and_is_not_cached(tmp_path, wav):
    empty = json.loads(json.dumps(CHAT_PAYLOAD))
    empty["choices"][0]["message"]["content"] = ""
    empty["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError, match="no answer text"):
        _call(tmp_path, FakeOpenClient(FakeCompletions(empty)))
    assert not list((tmp_path / "cache").glob("*.json"))
    assert len((tmp_path / "costs.jsonl").read_text().splitlines()) == 1
