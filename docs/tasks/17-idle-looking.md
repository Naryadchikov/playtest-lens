# 17: Tell looking around from being away

**Author:** Muse Code on Muse Wonder (`muse-wonder-1.0`), high effort, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: an idle stretch in the log says whether the player was looking around or away, using the new look direction in the log.

Sasha (T3 Code chat, 2026-10-27): "Keep Muse's idle and walk-back numbers until a real log shows how often they fire. Also log where the player looks (yaw and pitch, about twice a second), so idle can tell looking around from being away: standing still and looking around is the sign of a lost player."

Read AGENTS.md, "The analyzer's rules", and follow the `change-analyzer` skill (`.claude/skills/change-analyzer/SKILL.md`).

## What exists

- `analyzer/log_candidates.py` (task 13): `load_log`, `find_candidates`, and an `idle` kind: position samples within `IDLE_MAX_MOVE_M = 0.5` m, gaps up to `IDLE_MAX_GAP_S = 2.0` s, no `input` line, at least `IDLE_MIN_S = 10.0` s. Keep those numbers (Sasha's words above).
- The log's `position` line now also has `yaw` and `pitch` (degrees, from the camera the player sees through), every 0.5 s. Mouse and gamepad looking write no `input` lines. Older logs may have `yaw` only, or neither.
- `tests/fixtures/session_log.jsonl` is replaced in this commit by a new run of the same scripted session: in its 40 s stand, the player looks around for the first 20 s, then holds the view still for 20 s.

## What to build

- Split each idle stretch where the view starts or stops moving, and give each part a kind: `looking_around` (still, the view turning) or `idle` (still, the view still). Keep only parts at least `IDLE_MIN_S` long. Propose one rule for "the view is turning" (for example, more than some degrees between two samples, with yaw's wrap at 180 handled) and a number for it as a named constant; it's a proposal for Sasha.
- The `detail` says how much the view turned, as a plain fact.
- A log without `yaw` and `pitch` keeps today's behaviour: every still stretch is `idle`.
- Nothing else in the module changes.

## Files you own

- `analyzer/log_candidates.py`, `tests/test_log_candidates.py`

Touch nothing else. Don't commit.

## Tests (pytest, offline)

- On the new fixture: one `looking_around` covering about the first 20 s of the stand, then one `idle` covering about the last 20 s; the death, retry and backtrack as before.
- Hand-written cases: yaw going from 179 to -179 counts as 2 degrees, not 358; a log without `pitch` or `yaw` gives `idle` only.
- The existing tests still pass (`.venv/bin/python -m pytest -q`).

## Report back

The files changed, the commands with their output, your rule and number for "the view is turning", and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Never set, export or read `META_API_KEY` or any credential file. No API call.
- Install Python packages only into this checkout's `.venv` from `requirements.txt`; nothing else.
- Ignore the `game/` folder.
- No em dashes or spaced en dashes in anything you write.
