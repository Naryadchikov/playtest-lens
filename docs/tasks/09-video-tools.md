# 09: Cut a clip around a time, and find the start flash

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: one Python module that does all the video work with ffmpeg: convert, cut a 20-second clip around a time, and find the start flash, tested on synthetic video.

Sasha (T3 Code chat, 2026-10-26): "Grok, after that: tools for cutting a 20-second clip around a time and finding the start flash in a video, tested on synthetic video." And: "No API calls today except cent-sized tests on synthetic input."

## What exists

- `analyzer/spark_test.py` has `convert_video(recording, output_path, start=0.0, seconds=None)` (ffmpeg, H.264 720p max plus AAC, re-encoded so cuts are frame-accurate) and `probe_duration(path)`. Both were checked on synthetic video (docs/tasks/01-spark-test.md): a cut from 3 s starts on the 3.0 s frame, and a variable-frame-rate `.mov` keeps its times.
- The game's start flash (task 08): about 1 s after launch, the whole window pure white for 0.25 s, plus a 1000 Hz beep for 0.25 s. The log's `start_flash` line marks the frame it was drawn.

## Files you own

- `tools/__init__.py`, `tools/video.py` (new)
- `analyzer/spark_test.py`: only to remove `convert_video` and `probe_duration` and import them from `tools.video` (one path for video)
- `tests/test_video.py`

Touch nothing else. Don't commit.

## What `tools/video.py` has

- `probe_duration(path)` and `convert_video(...)`, moved unchanged from `analyzer/spark_test.py`.
- `cut_clip(recording, time_s, output_path, seconds=20.0)`: a clip centered on `time_s` (from `time_s - seconds/2`), clamped to the recording's start and end, using `convert_video`. Returns the `(start_s, end_s)` it actually used, so the pipeline can write them into `findings.json`.
- `find_start_flash(video, search_s=120.0)`: the time in seconds of the first frame in the first `search_s` seconds where the whole frame is near white (use ffmpeg's `signalstats`: the frame's minimum luma high, not only its average, so a white menu with dark text doesn't count). Returns that time. If there is none, raise `ValueError` with a clear message; never guess. Optionally, report where the 1000 Hz beep starts (for example `silencedetect` or a band-pass), but the flash is the answer.

Keep it to plain functions. No class, no config.

## Tests (pytest, offline, ffmpeg generates every video)

- `cut_clip`: on a 60 s `testsrc` video, a clip at 30 s runs 20.0 to 40.0 s and its first frame matches the source's 20.0 s frame (compare frames, as task 01's check did); a clip at 5 s is clamped to start at 0; one at 58 s is clamped to the end.
- `find_start_flash`: a dark synthetic recording at 60 fps, variable frame rate (drop some frames, as macOS screen recording does), with a full white frame block from 7.000 s to 7.250 s: found within one frame (1/60 s). A recording with a white menu screen that has dark text, and no full flash: raises `ValueError`. A 1080p and a 720p source both work.
- The existing tests still pass (`.venv/bin/python -m pytest -q`).

## Done means

- All tests pass, offline. Show the output.
- `analyzer/spark_test.py --help` still works, and `grep -n "def convert_video\|def probe_duration" -r analyzer tools` shows one definition of each, in `tools/video.py`.

## Report back

The files changed, the commands with their output, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Never set, export or read `META_API_KEY` or any credential file. No API call.
- Install Python packages only into this checkout's `.venv` (create it with `python3 -m venv .venv` and install `requirements.txt`). Prefer ffmpeg and the standard library.
- Ignore the `game/` folder.
- No em dashes or spaced en dashes in anything you write.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
