# 13: Candidate moments from the event log

**Author:** Muse Code on Muse Wonder (`muse-wonder-1.0`), high effort, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: one module reads a session's event log and returns its candidate moments (deaths, retries, long idle stretches, walking back the way you came), each with its time in the video. No model call.

Sasha (T3 Code chat, 2026-10-27): "The event-log candidates: deaths, retries, long idle stretches and walking back the way you came, read from the logger's JSONL, with log times mapped to video time through the flash. Test on logs from the game's headless tests. No API calls."

Read PLAN.md, "What we build", AGENTS.md, "The analyzer's rules", and follow the `change-analyzer` skill (`.claude/skills/change-analyzer/SKILL.md`).

## The log (written by the game's add-on)

One JSON object per line, each with `t` (seconds on one clock, from the logger's start) and `event`:

- `session_start` (first line), `session_end` (last, when the game quits cleanly; may be missing after a crash)
- `input`: `action`, `pressed`
- `scene`: `scene` (the scene file path); a reload of the same level writes a new `scene` line
- `position` every 0.5 s while the player exists: `x`, `y`, `z` (metres, y up), `yaw` (degrees)
- `sync_flash`: `reason` (`new_game` or `level_load`), `duration_s`, `beep_hz`; logged on the frame the white was drawn
- `death`; and COGITO's `door`, `lock`, `keypad`, `pickup`, `quest`

The test input is `tests/fixtures/session_log.jsonl`, a headless run of a real COGITO level: New Game, about 10 m out and back, about 40 s standing still, a death, a retry through the death screen, a few metres, quit.

## Lining up with the video

`tools/video.py`'s `find_start_flash(video)` gives the video time of the first white flash. Map a log time to video time as `video_t = log_t - first_flash_log_t + video_flash_s`, where `first_flash_log_t` is the first `sync_flash` line. A log with no `sync_flash` raises `ValueError` with a clear message; never guess.

## What to build

- `analyzer/log_candidates.py`: `load_log(path)` (parses and checks the lines, raising `ValueError` with the line number on a bad line; tolerates a missing `session_end`), and `find_candidates(events, video_flash_s)` returning a list of plain dicts sorted by `time_s`: `time_s` and `end_s` (video time, rounded to 0.01), `kind` (`death`, `retry`, `idle`, `backtrack`), and `detail` (a short plain fact from the log, for example the scene, or the distance walked back).
- Your definitions, with the numbers as named constants at the top of the module:
  - `death`: each `death` line.
  - `retry`: a `scene` line for the same level as the one the last `death` happened in.
  - `idle`: a stretch at least `IDLE_MIN_S` long with no `input` line and the player moving less than a small distance.
  - `backtrack`: the player walking back the way they came. Propose a simple rule (for example, coming back within a few metres of a point passed at least some seconds earlier, after having gone some distance past it), and keep it to one rule.
  The numbers are a proposal: list them in your report so the orchestrator can ask Sasha.
- A small CLI is not needed yet.

## Files you own

- `analyzer/log_candidates.py` (new), `tests/test_log_candidates.py` (new)
- `tests/fixtures/session_log.jsonl` is already there; don't edit it. Add small hand-written logs for edge cases inside the test file.

Touch nothing else. Don't commit.

## Tests (pytest, offline)

- On the fixture: one `death`, one `retry`, one `idle` covering the 40 s stand, one `backtrack` on the way back; their times map through the flash (check one by hand from the raw `t`).
- Edge cases: no `sync_flash` raises `ValueError`; a malformed line names its line number; no `session_end` still works; a log with no `position` lines gives no `idle` or `backtrack` and no error.
- The existing tests still pass (`.venv/bin/python -m pytest -q`).

## Report back

The files changed, the commands with their output, your rules and numbers for `idle` and `backtrack`, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Never set, export or read `META_API_KEY` or any credential file. No API call.
- Install Python packages only into this checkout's `.venv` (create it with `python3 -m venv .venv` and install `requirements.txt`). Standard library only for this module.
- Ignore the `game/` folder.
- No em dashes or spaced en dashes in anything you write.
