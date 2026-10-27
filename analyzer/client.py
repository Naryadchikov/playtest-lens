"""The one module that talks to the Meta Model API.

Every model call goes through here so replies are cached in runs/cache/
and every real call appends one line to runs/costs.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx2

BASE_URL = "https://api.meta.ai/v1"
DEFAULT_CACHE_DIR = Path("runs/cache")
DEFAULT_COSTS_PATH = Path("runs/costs.jsonl")

# USD per million tokens: (input, output). From the brief (Meta pricing).
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.2": (1.25, 4.25),
    "muse-wonder-1.0": (4.00, 20.00),
}

TRANSCRIBE_MODEL = "muse-voice-transcribe-1.0"
TRANSCRIBE_USD_PER_HOUR = 0.18

MISSING_KEY_MESSAGE = (
    "META_API_KEY is not set. Run via tools/run-analyzer.sh, "
    "which reads it from the macOS Keychain."
)


# Return the API key from the environment, or exit with a clear message.
def require_api_key() -> str:
    key = os.environ.get("META_API_KEY")
    if not key:
        print(MISSING_KEY_MESSAGE, file=sys.stderr)
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


def _extract_id(result) -> str:
    if isinstance(result, dict):
        return result["id"]
    return result.id


def _response_to_dict(response) -> dict:
    return response.model_dump()


# Pull the text out of a Responses API reply dict.
def extract_text(response: dict) -> str:
    if not isinstance(response, dict):
        return ""
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    parts = []
    for item in response.get("output") or []:
        if not isinstance(item, dict):
            continue
        for block in item.get("content") or []:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
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


# Send one video plus prompt in one Responses call, with caching and cost logging.
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

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(reply, indent=2), encoding="utf-8")

    audio_s = reply["audioDurationMs"] // 1000
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
