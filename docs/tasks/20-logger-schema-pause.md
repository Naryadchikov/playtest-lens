# Task 20: Logger schema, pause lines, perf lines, marker key

Author: Muse Wonder (Muse Code in T3 Code). Reviewer: Grok 4.7 (xhigh, fast) through Cursor, as part of the full review after task 19.

## Goal

Everything that can land before Sasha's next COGITO session, from the telemetry research handoff (2026-10-28): pause and resume lines so paused time never reads as idle, a versioned session header so logs from different builds can be told apart, a once-a-second perf line, an F9 marker, and the schema written down.

## Files

- game/addons/playtest_lens/logger.gd and its headless test (fork, `playtest-lens` branch)
- analyzer/log_candidates.py and tests/test_log_candidates.py
- docs/LOG_SCHEMA.md, docs/PRIOR_WORK.md

## Done means

- `session_start` carries `schema: 1`, `session_id`, `os` and `renderer`; `session_end` carries `reason`.
- The logger writes `pause`, `resume`, `perf` (fps, frame_ms) and `marker` (F9) lines, listening only.
- The analyzer rejects a schema newer than 1 and never counts paused time as idle or as a backtrack.
- The Godot headless tests pass and the Python tests pass.
