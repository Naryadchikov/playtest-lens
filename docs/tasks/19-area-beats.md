# Task 19: Area, Puzzle, Attempt grouping

Author: Muse Wonder (Muse Code in T3 Code). Reviewer: Grok 4.7 (xhigh, fast) through Cursor.

## Goal

Group report findings the way Sasha described on 2026-10-28: Area, then Puzzle, then Attempt, then the kept moments as Sub-beats. A return to the same Puzzle after solving something else is Attempt 2, even when it happens soon after.

## Files

- analyzer/beats.py
- analyzer/check.py
- analyzer/prompts/check.md
- report/render.py
- tests/test_beats.py, tests/test_check.py, tests/test_report.py
- tests/fixtures/check_reply.json
- DECISIONS.md, STATUS.md

## Done means

- The checker returns a stable area label as well as a puzzle label.
- Beats carry area, puzzle, puzzle_number, attempt, attempt_start_s and attempt_end_s.
- The report shows one distinct beat header per Area, Puzzle and Attempt.
- The Talos rerun groups the 7:24 fan beat as Attempt 1 and the return after the intervening solve as Attempt 2.
- Offline tests pass, Grok reviews the diff, and the work is committed and pushed.
