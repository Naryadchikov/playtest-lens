import json
import shutil
import subprocess
from pathlib import Path

import pytest

import httpx2

from analyzer import client
from analyzer import transcribe as transcribe_cli
from tools.video import extract_audio, probe_duration

FIXTURE = Path(__file__).parent / "fixtures" / "transcribe_reply.json"


def _audio(tmp_path, name="clip.wav", content=b"fake-wav-bytes"):
    path = tmp_path / name
    path.write_bytes(content)
    return path


def _reply():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_transcribe_request_cache_and_cost(tmp_path):
    audio = _audio(tmp_path)
    cache_dir = tmp_path / "cache"
    costs = tmp_path / "costs.jsonl"
    seen = []

    def handler(request):
        seen.append(request)
        return httpx2.Response(200, json=_reply())

    transport = httpx2.MockTransport(handler)
    http_client = httpx2.Client(transport=transport)
    reply = client.transcribe(
        audio,
        purpose="transcribe:clip.wav",
        cache_dir=cache_dir,
        costs_path=costs,
        api_key="test",
        http_client=http_client,
    )
    assert reply == _reply()
    assert len(seen) == 1

    request = seen[0]
    assert str(request.url) == "https://api.meta.ai/v1/asr/transcribe"
    assert request.headers["authorization"] == "Bearer test"
    assert request.headers["accept"] == "application/json"
    body = request.read()
    assert b'name="request"' in body
    assert b'name="audio"' in body
    assert b"muse-voice-transcribe-1.0" in body
    assert b'"audioEncoding": "WAV"' in body or b'"audioEncoding":"WAV"' in body
    assert b'"mode": "ENDPOINTING"' in body or b'"mode":"ENDPOINTING"' in body
    assert b"languageBias" not in body
    assert b"fake-wav-bytes" in body
    assert b"clip.wav" in body

    lines = costs.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["model"] == "muse-voice-transcribe-1.0"
    assert entry["input_tokens"] is None
    assert entry["output_tokens"] is None
    assert entry["audio_s"] == 20
    assert entry["cost_usd"] == pytest.approx(20 * 0.18 / 3600)
    assert entry["purpose"] == "transcribe:clip.wav"
    assert "time" in entry

    # Second call is a cache hit: no request, no new cost line.
    reply2 = client.transcribe(
        audio,
        purpose="transcribe:clip.wav",
        cache_dir=cache_dir,
        costs_path=costs,
        api_key="test",
        http_client=http_client,
    )
    assert reply2 == _reply()
    assert len(seen) == 1
    assert len(costs.read_text(encoding="utf-8").strip().splitlines()) == 1
    http_client.close()


def test_transcribe_same_content_new_path_is_cache_hit(tmp_path):
    first = _audio(tmp_path, name="a.wav")
    second = _audio(tmp_path, name="b.wav")
    cache_dir = tmp_path / "cache"
    costs = tmp_path / "costs.jsonl"
    calls = []

    def handler(request):
        calls.append(request)
        return httpx2.Response(200, json=_reply())

    http_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client.transcribe(
        first, "transcribe:a.wav", cache_dir=cache_dir, costs_path=costs,
        api_key="test", http_client=http_client,
    )
    client.transcribe(
        second, "transcribe:b.wav", cache_dir=cache_dir, costs_path=costs,
        api_key="test", http_client=http_client,
    )
    assert len(calls) == 1
    http_client.close()


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[-800:])
    return result


@pytest.mark.skipif(shutil.which("say") is None, reason="macOS say is not available")
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not available")
def test_extract_audio_from_say_clip(tmp_path):
    aiff = tmp_path / "speech.aiff"
    text = (
        "Hello world. This is a synthetic speech clip for testing. "
        "The player is trying to open the door. It will not open. "
        "Maybe there is a key somewhere nearby. Let us look around."
    )
    _run(["say", "-o", str(aiff), text])
    duration = probe_duration(aiff)
    assert duration is not None and duration > 7

    video = tmp_path / "speech.mp4"
    _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:r=10",
            "-i", str(aiff),
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(video),
        ]
    )

    out = tmp_path / "cut.wav"
    result_path = extract_audio(video, out, start=2.0, seconds=5)
    assert result_path == out
    assert probe_duration(out) == pytest.approx(5.0, abs=0.15)

    probe = _run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels,bits_per_sample",
            "-of", "json", str(out),
        ]
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert stream["codec_name"] == "pcm_s16le"
    assert int(stream["sample_rate"]) == 16000
    assert int(stream["channels"]) == 1
    assert int(stream["bits_per_sample"]) == 16


def test_missing_key_stops_cli_before_any_work(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("META_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        transcribe_cli.main(["missing.mp4"])
    assert excinfo.value.code == 1
    assert client.MISSING_KEY_MESSAGE in capsys.readouterr().err
    assert not (tmp_path / "runs" / "transcribe").exists()
