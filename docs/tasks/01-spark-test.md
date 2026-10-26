# 01: The Spark test

**Author:** Muse Code on Muse Wonder (`muse-wonder-1.0`), high effort, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: a script that sends one playtest recording (screen plus the player's voice) to Muse Spark in one call and saves the moments where the player was confused, stuck or surprised, each with a time and a reason, as JSON in `runs/`. It decides go or no-go for the project (PLAN.md, "Days", Tue Oct 27).

Sasha's words (T3 Code chat, 2026-10-26): the script "sends the recording to Muse Spark 1.3, video and audio in one call, downscaled with ffmpeg if the API's limits need it; gets back the moments where the player was confused, stuck or surprised, each with a time and a reason; saves them as JSON in runs/." The test passes "if 7 of the first 10 are real, within about 5 seconds."

Follow the `change-analyzer` skill (`.claude/skills/change-analyzer/SKILL.md`) and AGENTS.md, "Access and cost" and "The analyzer's rules".

## Files you own

- `analyzer/__init__.py`
- `analyzer/client.py`: the one model client
- `analyzer/spark_test.py`: the script
- `analyzer/prompts/spark_test.md`: the prompt
- `tests/test_client.py`, `tests/test_spark_test.py`, `tests/fixtures/`
- `requirements.txt`

Touch nothing else. Don't commit.

## What Meta's docs say (checked by the orchestrator, 2026-10-26)

- Base URL `https://api.meta.ai/v1`, OpenAI-compatible; the docs use the `openai` Python package and the Responses API (`client.responses.create`).
- Video: `video/mp4` only. Send it with the Files API (`POST /v1/files`, `purpose="user_data"`, up to 1 GiB), then an `input_video` block with `file_id`. Inline data URLs are capped at 50 MB, too small for 15 minutes. Spark reads the video's embedded audio.
- Context window 1,048,576 tokens for input and output together. Meta publishes no per-second video token cost, so measure it from the usage the reply returns.
- `muse-spark-1.3`: $1.25 in, $4.25 out, $0.15 cached input per million tokens. Meta's model page says "Audio understanding in Muse Spark 1.3 is not fully supported" and recommends `muse-spark-1.2` (same price) for audio.
- Docs: https://dev.meta.ai/docs/video-understanding, /docs/file-handling, /docs/models, /docs/pricing-rate-limits. Check them yourself if anything here doesn't match what the API does, and say so.

## What to build

**`analyzer/client.py`**, the only place that talks to the API:
- Reads `META_API_KEY` from the environment. If it's missing, exit with a clear message. Never print, log or write the key.
- Uploads a file and returns its id. Remember the id by the file's content hash, so the same file isn't uploaded twice.
- Sends a request. The cache key is a SHA-256 of the request with each file replaced by its content hash (file ids differ per upload; the content doesn't). A cache hit returns the saved reply from `runs/cache/` and makes no network call.
- After every real call, appends one JSON line to `runs/costs.jsonl`: time, model, input and output tokens, cost in USD (from the reply if given, else from a small price table for the models above), and a `purpose` string the caller passes. A cache hit adds no line.
- No retries framework, no async, no class hierarchy. A few functions are enough.

**`analyzer/spark_test.py`**, run as `tools/run-analyzer.sh analyzer/spark_test.py <recording> [--model muse-spark-1.3] [--seconds N]`:
- Converts the recording with ffmpeg to an mp4 (H.264 video, AAC audio, 720p at most) in a temp folder outside the repo or under `runs/`. Recordings from a Mac are `.mov`, so always convert. `--seconds N` keeps only the first N seconds (for the 30-second test).
- Sends it with the prompt from `analyzer/prompts/spark_test.md` in one call, video and audio together.
- The prompt asks for JSON only: a list of moments, each `{"time_s": number, "kind": "confused" | "stuck" | "surprised", "reason": string, "quote": string or null}`, ordered by how sure the model is, most sure first. Times are seconds from the start of the video.
- Parses the reply. If it isn't valid JSON of that shape, save the raw reply and exit with a clear error. Never guess a time.
- Writes `runs/spark_test/<recording name>-<model>.json` with the moments, the model, the input file's hash and duration, and the usage.
- `--model` exists so the orchestrator can compare `muse-spark-1.3` with `muse-spark-1.2` on the same cut, given the audio caveat above. Default `muse-spark-1.3`.

**Tests** (pytest), offline, with no key and no network:
- a cached reply in `tests/fixtures/` is returned without a network call and adds no cost line;
- the cache key is the same for the same file content uploaded under two different file ids;
- a real call (mocked transport) adds exactly one cost line with the right fields and cost;
- the parser accepts a good reply, and rejects a reply with no JSON or a moment without a time with a clear error.

## Done means

- `.venv/bin/python -m pytest -q` passes, offline. Show the output.
- `.venv/bin/python analyzer/spark_test.py --help` works.
- Running it with no `META_API_KEY` exits with the clear message, before any upload.
- No real API call during the task. You can't make one anyway: the key isn't in your environment, and must stay out of it. The orchestrator runs the first real call on a 30-second cut.

## Report back

The files changed, the commands you ran and their output, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Install Python packages only into this folder's `.venv` (create it with `python3 -m venv .venv` if it's missing). Install nothing system-wide.
- Never read or print credential files (`~/.config/muse/`). Never set or export `META_API_KEY`.
- No em dashes or spaced en dashes in anything you write.
- The repo is public: no keys, tokens, recordings or private files.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
