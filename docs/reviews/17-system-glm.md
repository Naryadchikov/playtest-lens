Reviewer: fresh reviewer, GLM 5.3, Claude Code in T3 Code, commits 75777b5 + e16826d + f63a455 on main (base 31e07d7, tasks docs/tasks/27-fixes-now.md and docs/tasks/28-system-pass.md; authors Opus 5.5 for the first two, Grok 4.7 for the third).

**PASS**

## What I checked

- `.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip`: 191 passed, 1 deselected, exit 0. The four new merge tests and the old no-zones merge test all pass.
- One finding path: `merge_same_moment` is called exactly once (`analyzer/check.py:390`, in `main`, after `run_checks`, before `assign_beats`); `analyzer/beats.py` standalone only calls `assign_beats` and never merges or creates a finding. The report is untouched by this diff; `report/render.py` reads `end_s` with `get` for display only and computes nothing.
- Every model call still goes through `analyzer/client.py`: the diff adds no network code, and `check.py` / `spark_test.py` still call only `call_model` and `transcribe`.
- `verified_quote` is unchanged in the diff and still applied to every check quote (`analyzer/check.py:224`). The new prompt wording ("copied word for word from the transcript, or null") narrows, not weakens.
- No key, token or private path in the diff (scanned for `api_key`, `token`, `secret`, `sk-`, `Bearer`: nothing). No em dash or spaced en dash in the diff bytes.
- Each commit stayed inside its task's file list: `f63a455` did not touch `analyzer/prompts/check.md`, which task 28 forbade. The prompt rewrite in `75777b5` is Opus's own, documented in task 27's "What came back" section; the JSON reply line keeps its doubled braces and every placeholder, and `spark_test.md` still names no engine.

## The four judged points

- **Visit merge, 8 seconds only without a zone.** `merge_same_moment(findings, zones=None)` groups kept findings by `(zone, puzzle, start_s, kind)`, folding one kind across a whole visit however long it is; the 8-second `MERGE_WINDOW_S` chain runs only in the `place is None` branch. `main` computes `zone_intervals` once and passes the same list to `merge_same_moment` and `assign_beats`. A re-entry is a new visit (the `start_s` in the key differs), proven by `test_merge_same_moment_starts_again_after_the_player_reenters`.
- **A puzzle box inside a room is not folded into the room.** `_place` prefers covering zones with a non-empty `puzzle`, else the latest `start_s`, matching the logger. `test_merge_same_moment_prefers_the_puzzle_box_inside_the_room` proves it: two stucks inside the Code Lock interval fold, the room-only stuck stays its own card with `end_s` still None.
- **Window overlap is 20 seconds.** `WINDOW_OVERLAP_S = 20.0`; starts advance by `window_s - 20`, so adjacent windows overlap by exactly 20 s, and any 20 s clip fits whole inside one window (proven by the edge test at 98, 101, 119, 121, 238, 242, 505 and 915 s). A window of 20 s or less is refused, both in `window_starts` (ValueError) and in the CLI guard.
- **`log_slice_text` carries zones already open.** A zone entered before the clip and not exited before it (or still open) gets one `[video Xs, before this clip, still open]` line at the top; a zone closed before the clip is not carried; a zone entered inside the clip prints exactly as before, with no duplicate carry line (the `start_s < start_s` condition excludes it).

## Blocking findings

None.

## Nits

1. `analyzer/check.py`, `merge_same_moment`: the no-zone 8-second chain (`open_group`) is never reset when a zone visit intervenes. Example: a stuck at t=10 in a corridor (no zone), a stuck at t=14 inside a room, a stuck at t=18 in a corridor again: the t=18 card chains into the t=10 group (18 - 10 = 8) and the two corridor cards fold into one, even though a whole room visit separates them. The visit rule's intent says the corridor struggle ended at the room door. No test covers a no-zone, in-zone, no-zone sequence. Not blocking: this is strictly less folding than the old code, which merged all three into one card, and it needs two corridor findings within 8 s across a visit boundary.
2. `analyzer/check.py`, `log_slice_text`: `beats.zone_intervals(events, ...)` is recomputed for every candidate clip, and `main` computes the same list again just before. It is the same implementation called again (not a second tracker), only duplicate work; harmless at real sizes.
3. `tests/test_check.py`: no test for a zone still open at the clip start that exits inside the clip. The code handles it (the carry condition `end_s >= start_s` holds, so the carried line and the real `zone_exit` line appear in the same slice, which is the correct story), but nothing pins it. Same for `_place` when two puzzle zones overlap (latest start wins, untested); both are one-line cases if they are ever worth pinning.
