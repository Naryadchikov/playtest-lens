# 11: The Voice Transcribe client for one 20-second clip

**Author:** Muse Code on Muse Wonder (`muse-wonder-1.0`), high effort, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: the analyzer can send the audio of one 20-second clip to Muse Voice Transcribe and get back what was said, cached and costed like every other call. Tested offline; the one real call is the orchestrator's.

Sasha (T3 Code chat, 2026-10-27): "The Voice Transcribe client for one 20-second clip, tested on a synthetic speech clip (macOS `say`). Cents only." And how the product uses it (2026-10-26): "Voice Transcribe stays, used per candidate: transcribe each 20-second clip, so the report's quotes are what I actually said and the check gets my words as text. The times come from Spark and the clip's place in the video."

Read AGENTS.md, "Access and cost" and "The analyzer's rules", and follow the `change-analyzer` skill (`.claude/skills/change-analyzer/SKILL.md`).

## The API (from Meta's docs, read 2026-10-27; check them yourself)

- https://dev.meta.ai/docs/speech-to-text and https://dev.meta.ai/docs/api-reference/voice/transcribe
- `POST https://api.meta.ai/v1/asr/transcribe`, `Authorization: Bearer <key>`, `multipart/form-data` with two parts: `request` (JSON settings) and `audio` (the file). Not part of the `openai` SDK's methods.
- Settings: `model` `muse-voice-transcribe-1.0`, `audioEncoding` `WAV`, `mode` `PUSH_TO_TALK` (default), `ENDPOINTING` or `DIARIZATION`. Use `ENDPOINTING`: it returns turns with times. Leave `languageBias` out (testers may not speak English).
- Audio: RIFF WAV, mono, 16-bit PCM, 16 or 24 kHz. Up to 10 minutes and 32 MB.
- Response (`Accept: application/json`): `sessionId`, `transcript`, `audioDurationMs`, `turns` (each `turnId`, `startMs`, `endMs`, `transcript`, `speaker`). No `usage` field. No word-level times.
- Price: $0.18 per hour of audio, billed on the audio processed, rounded down to whole seconds.

## Files you own

- `analyzer/client.py`: a `transcribe(...)` function next to `call_model`, sharing its cache and its cost line (one client module, one cache, one cost log). Add the price to `PRICES`.
- `tools/video.py`: only an `extract_audio(video, output_path, start=0.0, seconds=None)` that writes the WAV the API takes (ffmpeg, `-ss` before `-i` as `convert_video` does). One path for media work.
- `analyzer/transcribe.py` (new): a small CLI, `python -m analyzer.transcribe <video> [--start S] [--seconds N]`, that extracts the audio, calls `transcribe`, and writes the reply with the clip's start and length to `runs/transcribe/<stem>-from{start}s-{seconds}.json`. Requires the key first, like `analyzer/spark_test.py`.
- `tests/test_transcribe.py`, and fixtures under `tests/fixtures/` (a JSON reply only; no audio file in the repo)

Touch nothing else. Don't commit.

## What "cached and costed" means here

- The cache key hashes the settings JSON and the audio file's content hash (not its path), so a rerun on the same clip costs nothing and makes no request.
- Each real call appends one line to `runs/costs.jsonl` with the same fields as `call_model`'s line, `input_tokens` and `output_tokens` as null, plus `audio_s` (whole seconds, from `audioDurationMs` rounded down) and `cost_usd` from that.
- Never print, log or write the key, and never put it in a URL.

## Tests (pytest, offline, no API call, no key)

- `transcribe` with a fake HTTP layer (for example an `httpx.MockTransport`, or the injection `call_model` already uses): the request has the two parts, the right settings and the bearer header; the reply is cached; a second call makes no request; the cost line has `audio_s` and the right `cost_usd` (20.9 s of audio bills 20 s).
- `extract_audio`: on a synthetic speech clip made with macOS `say` and muxed into an mp4 with a video track, a cut from 2 s for 5 s gives a mono 16-bit WAV at the rate you chose, 5.0 s long. Skip the test with a clear reason when `say` isn't there.
- A missing key stops the CLI with `MISSING_KEY_MESSAGE` before any ffmpeg or network work.
- The existing tests still pass (`.venv/bin/python -m pytest -q`).

## Done means

- All tests pass, offline. Show the output.
- `python -m analyzer.transcribe --help` works.
- A short note of the exact command the orchestrator should run for the one real call: a 20-second mp4 made from `say` speech, run through `tools/run-analyzer.sh -m analyzer.transcribe ...`. Don't run it yourself: the key stays out of your environment.

## Report back

The files changed, the commands with their output, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Never set, export or read `META_API_KEY` or any credential file. No API call.
- Install Python packages only into this checkout's `.venv` (create it with `python3 -m venv .venv` and install `requirements.txt`). Prefer what's there: `openai` brings `httpx`.
- Ignore the `game/` folder.
- No em dashes or spaced en dashes in anything you write.
