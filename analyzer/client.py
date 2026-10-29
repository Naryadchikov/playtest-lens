"""The one module that talks to the model APIs.

Muse Spark and Voice Transcribe go to the Meta Model API. A model id that
starts with OPEN_WEIGHTS_PREFIX goes to Baseten instead, as video plus a wav.
Every model call goes through here so replies are cached in runs/cache/
and every real call appends one line to runs/costs.jsonl.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx2

from tools.video import extract_audio

BASE_URL = "https://api.meta.ai/v1"
OPEN_WEIGHTS_PREFIX = "meta-models/"
BASETEN_BASE_URL = "https://inference.baseten.co/v1"
DEFAULT_CACHE_DIR = Path("runs/cache")
DEFAULT_COSTS_PATH = Path("runs/costs.jsonl")

# USD per million tokens: (input, output). Meta prices from the brief and
# dev.meta.ai/docs/pricing-rate-limits (the contributor rows); the open-weights
# row is Baseten's public Model APIs table (baseten.co/pricing).
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.2": (1.25, 4.25),
    "muse-spark-1.2-contributor": (0.10, 0.20),
    "muse-wonder-1.0": (4.00, 20.00),
    "meta-models/muse-spark-open-1026": (1.25, 4.25),
}

TRANSCRIBE_MODEL = "muse-voice-transcribe-1.0"
TRANSCRIBE_USD_PER_HOUR = 0.18

# The model's reasoning counts against max_tokens. 4096 was used up
# before the answer on a 2-minute window, so leave more room.
OPEN_MAX_TOKENS = 8192

MISSING_KEY_MESSAGE = (
    "META_API_KEY is not set. Run via tools/run-analyzer.sh, "
    "which reads it from the macOS Keychain."
)
MISSING_BASETEN_KEY_MESSAGE = (
    "BASETEN_API_KEY is not set. Run via tools/run-baseten.sh, "
    "which reads it from the macOS Keychain."
)

# A chat reply can start with a stray token marker such as <|start|>assistant.
LEADING_CHAT_MARKER = re.compile(r"^(?:\s*<\|[^|]*\|>)+\s*(?:assistant)?\s*")


# Return the API key from the environment, or exit with a clear message.
def require_api_key() -> str:
    key = os.environ.get("META_API_KEY")
    if not key:
        print(MISSING_KEY_MESSAGE, file=sys.stderr)
        raise SystemExit(1)
    return key


# Return the Baseten key from the environment, or exit with a clear message.
def require_baseten_key() -> str:
    key = os.environ.get("BASETEN_API_KEY")
    if not key:
        print(MISSING_BASETEN_KEY_MESSAGE, file=sys.stderr)
        raise SystemExit(1)
    return key


# SHA-256 of a file's bytes.
def file_content_hash(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_client(api_key=None):
    from openai import OpenAI

    return OpenAI(base_url=BASE_URL, api_key=api_key or require_api_key())


def _make_open_client(api_key=None):
    from openai import OpenAI

    return OpenAI(
        base_url=BASETEN_BASE_URL, api_key=api_key or require_baseten_key()
    )


# Strip a leading chat token marker so extract_text sees the answer alone.
def strip_assistant_marker(text: str) -> str:
    return LEADING_CHAT_MARKER.sub("", text.strip(), count=1)


# Turn an OpenAI chat reply into the dict shape extract_text and
# usage_and_cost read. Only message.content is the answer, never reasoning.
def _open_reply_to_dict(response) -> dict:
    data = _response_to_dict(response)
    choices = data.get("choices") or []
    message = {}
    finish_reason = None
    if choices:
        message = choices[0].get("message") or {}
        finish_reason = choices[0].get("finish_reason")
    usage = data.get("usage") or {}
    return {
        "id": data.get("id"),
        "model": data.get("model") or "",
        "output_text": strip_assistant_marker(message.get("content") or ""),
        "finish_reason": finish_reason,
        "usage": {
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
        },
    }


def _extract_id(result) -> str:
    if isinstance(result, dict):
        return result["id"]
    return result.id


def _response_to_dict(response) -> dict:
    return response.model_dump()


# Pull the text out of a Responses API reply dict.
# Only message items and their output_text blocks count: reasoning
# items are the model's private notes, not its answer.
def extract_text(response: dict) -> str:
    if not isinstance(response, dict):
        return ""
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    parts = []
    for item in response.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for block in item.get("content") or []:
            if (
                isinstance(block, dict)
                and block.get("type") == "output_text"
                and isinstance(block.get("text"), str)
            ):
                parts.append(block["text"])
    if parts:
        return "".join(parts)
    return ""


# Return (input_tokens, output_tokens, cost_usd) for a model and reply dict.
def usage_and_cost(model: str, response: dict):
    usage = response.get("usage") or {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cost = response.get("cost_usd", response.get("cost"))
    if cost is None:
        cost = usage.get("cost_usd", usage.get("cost"))
    if cost is None:
        cost = compute_cost(model, input_tokens, output_tokens)
    return input_tokens, output_tokens, cost


# Cost in USD from the price table, or None for an unknown model.
def compute_cost(model: str, input_tokens: int, output_tokens: int):
    if model not in PRICES:
        return None
    in_price, out_price = PRICES[model]
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


# Cost in USD for whole seconds of transcribed audio.
def transcribe_cost_usd(audio_s: int):
    return audio_s * TRANSCRIBE_USD_PER_HOUR / 3600.0


def _upload_index_path(cache_dir: Path) -> Path:
    return cache_dir / "uploads.json"


def _load_upload_index(cache_dir: Path) -> dict:
    path = _upload_index_path(cache_dir)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _save_upload_index(cache_dir: Path, index: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _upload_index_path(cache_dir).write_text(
        json.dumps(index, indent=2, sort_keys=True), encoding="utf-8"
    )


# Upload a file once per content hash and return its file id.
def upload_file(path, *, client=None, cache_dir=DEFAULT_CACHE_DIR, api_key=None) -> str:
    cache_dir = Path(cache_dir)
    content_hash = file_content_hash(path)
    index = _load_upload_index(cache_dir)
    if content_hash in index:
        return index[content_hash]
    if client is None:
        client = _make_client(api_key)
    with open(path, "rb") as handle:
        result = client.files.create(file=handle, purpose="user_data")
    file_id = _extract_id(result)
    index[content_hash] = file_id
    _save_upload_index(cache_dir, index)
    return file_id


# Append one real call as a line in runs/costs.jsonl.
def _append_cost_line(costs_path, *, model, reply, purpose) -> None:
    input_tokens, output_tokens, cost = usage_and_cost(model, reply)
    costs_path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "time": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "purpose": purpose,
    }
    with open(costs_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")


# Send one video plus prompt in one call, with caching and cost logging.
# A model id under OPEN_WEIGHTS_PREFIX goes to Baseten as video plus a wav;
# every other model goes to the Responses API with the video file.
def call_model(
    *,
    model: str,
    prompt: str,
    video_path,
    purpose: str,
    cache_dir=DEFAULT_CACHE_DIR,
    costs_path=DEFAULT_COSTS_PATH,
    client=None,
    api_key=None,
) -> dict:
    cache_dir = Path(cache_dir)
    costs_path = Path(costs_path)
    video_path = Path(video_path)
    if model.startswith(OPEN_WEIGHTS_PREFIX):
        return _call_open_model(
            model=model,
            prompt=prompt,
            video_path=video_path,
            purpose=purpose,
            cache_dir=cache_dir,
            costs_path=costs_path,
            client=client,
            api_key=api_key,
        )
    content_hash = file_content_hash(video_path)
    request = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_video", "file_id": content_hash},
                ],
            }
        ],
    }
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if client is None:
        client = _make_client(api_key)
    file_id = upload_file(video_path, client=client, cache_dir=cache_dir, api_key=api_key)
    request["input"][0]["content"][1]["file_id"] = file_id
    response = client.responses.create(model=model, input=request["input"])
    reply = _response_to_dict(response)

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(reply, indent=2), encoding="utf-8")
    _append_cost_line(costs_path, model=model, reply=reply, purpose=purpose)
    return reply


# Video and its audio as a wav, plus the prompt, to one Baseten chat call.
# Baseten ignores the sound inside the mp4, so the wav goes as its own part.
def _call_open_model(
    *, model, prompt, video_path, purpose, cache_dir, costs_path, client, api_key,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="open-audio-") as tmp:
        wav_bytes = extract_audio(video_path, Path(tmp) / "clip.wav").read_bytes()
    video_bytes = Path(video_path).read_bytes()
    request = {
        "model": model,
        "prompt": prompt,
        "video_sha256": hashlib.sha256(video_bytes).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_bytes).hexdigest(),
        "max_tokens": OPEN_MAX_TOKENS,
    }
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if client is None:
        client = _make_open_client(api_key)
    video_url = "data:video/mp4;base64," + base64.b64encode(video_bytes).decode("ascii")
    content = [
        {"type": "video_url", "video_url": {"url": video_url}},
        {
            "type": "input_audio",
            "input_audio": {"data": base64.b64encode(wav_bytes).decode("ascii"), "format": "wav"},
        },
        {"type": "text", "text": prompt},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=OPEN_MAX_TOKENS,
    )
    reply = _open_reply_to_dict(response)

    # The reasoning can use the whole token budget and leave no answer: the
    # tokens were billed, so log them, but never cache a reply with no text.
    if not reply["output_text"].strip():
        _append_cost_line(costs_path, model=model, reply=reply, purpose=purpose)
        raise ValueError(
            "The open model returned no answer text "
            f"(finish_reason {reply.get('finish_reason')!r}): its reasoning may have used the whole token budget."
        )

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(reply, indent=2), encoding="utf-8")
    _append_cost_line(costs_path, model=model, reply=reply, purpose=purpose)
    return reply


# Transcribe one WAV clip with Muse Voice Transcribe, cached and costed.
def transcribe(
    audio_path,
    purpose,
    *,
    cache_dir=DEFAULT_CACHE_DIR,
    costs_path=DEFAULT_COSTS_PATH,
    api_key=None,
    http_client=None,
) -> dict:
    cache_dir = Path(cache_dir)
    costs_path = Path(costs_path)
    audio_path = Path(audio_path)
    content_hash = file_content_hash(audio_path)
    settings = {"model": TRANSCRIBE_MODEL, "audioEncoding": "WAV", "mode": "ENDPOINTING"}
    canonical = json.dumps(
        {"request": settings, "audio_sha256": content_hash},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    key_value = api_key or require_api_key()
    own_client = http_client is None
    http = http_client if http_client is not None else httpx2.Client(timeout=120.0)
    try:
        files = {
            "request": (None, json.dumps(settings), "application/json"),
            "audio": (audio_path.name, audio_path.read_bytes(), "audio/wav"),
        }
        headers = {
            "Authorization": f"Bearer {key_value}",
            "Accept": "application/json",
        }
        response = http.post(f"{BASE_URL}/asr/transcribe", headers=headers, files=files)
        response.raise_for_status()
        reply = response.json()
    finally:
        if own_client:
            http.close()

    duration_ms = reply.get("audioDurationMs") if isinstance(reply, dict) else None
    if (
        isinstance(duration_ms, bool)
        or not isinstance(duration_ms, (int, float))
        or not math.isfinite(duration_ms)
        or duration_ms < 0
    ):
        raise ValueError("Transcribe reply has no numeric audioDurationMs.")
    audio_s = int(duration_ms // 1000)

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(reply, indent=2), encoding="utf-8")
    line = {
        "time": datetime.now(timezone.utc).isoformat(),
        "model": TRANSCRIBE_MODEL,
        "input_tokens": None,
        "output_tokens": None,
        "cost_usd": transcribe_cost_usd(audio_s),
        "purpose": purpose,
        "audio_s": audio_s,
    }
    costs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(costs_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")
    return reply
