# 23c: The report's "Across players" data, written by the summary step

**Author:** DeepSeek V4.1 Flash 1017 on Modal, `tools/run-modal-agent.sh deepseek`, inside worktree `.worktrees/ds-23c` (branch `ds/23c-cross`).
**Briefed by:** the orchestrator, Claude Sonnet 5.5 in Claude Code in T3 Code, 2026-10-28. **Reviewer:** Grok 4.7 xhigh through Cursor, fresh.
**Base commit:** the commit that adds this file. Runs in parallel with task 23b (route, heat, pins, summary from the log), which owns `analyzer/spatial.py` and `analyzer/check.py`; you do not touch them.

## Why

The report page (task 23, merged) has an "Across players" section that renders a `cross_player` block in each session's `findings.json`, but nothing writes it. The cross-player step (`analyzer/summary.py`) already groups kept findings across sessions; it must also write each session's own view of those groups into that session's file, because the page only renders the file. Sasha, T3 Code chat, 2026-10-28: "you can do your next task, and I will setup volumes on top afterwards".

## Outcome

`analyzer/summary.py` gets a function `cross_player(sessions_data)` that returns, for each session in the batch, the list the page expects, and a CLI flag `--write-cross-player` that rewrites each given findings file with its `cross_player` field (in place, validated afterwards with `analyzer.findings.load`; with `-o` not needed). The existing `summarize` output and its tests stay unchanged. No model call.

Shape (the page's contract, from `docs/tasks/23-report-redesign.md`): `cross_player: [{place: string, kind: string, of: int, players: [{label: string, moments: [finding ids], worst_t: number, here: bool}]}]`.

- One entry per shared group (seen in two or more sessions of the batch), using the grouping `summarize` already does (same kind, same place key). Single-session groups are not written. With only one session in the batch, write no `cross_player` field at all (the page hides the section when it is absent). Remove a stale `cross_player` from a file when the batch no longer has shared groups.
- `kind`: the group's kind. `of`: the number of sessions in the batch.
- `place`: a short readable place text from the group's first moment in rank order: the beat's area and puzzle joined as `"{area}, {puzzle}"` (as written in the file; only the first letter capitalised), the area alone or the puzzle alone when only one exists, else the finding's `game_state`. Keep it in one small function and say in a comment that the wording is Sasha's to change.
- `players`: one item per session in the group, in session order of the batch: `label` is `session.player` when present, else `session.id`; `moments` the ids of its kept findings in that group in rank order; `worst_t` the `time_s` of its finding in the group with the longest span (`end_s - time_s`, a missing `end_s` counts as 0; ties go to the earliest `time_s`); `here` is true only for the session the file belongs to. Each file gets its own `here`.
- Ordering of entries: the same as `summarize`'s group order (most sessions first, then kind, then game_state).
- Running it twice gives the same files (idempotent). Everything else in a file stays byte-for-byte the same except that JSON is re-serialised with `indent=2`, and the findings file is loaded and checked before and after.

Read first: `analyzer/summary.py`, `analyzer/findings.py` (the `cross_player` check the loader already does), `tests/test_summary.py`, `tests/fixtures/findings_sample.json` and `findings_sample_b.json`, and `AGENTS.md` ("The analyzer's rules").

## Files you own

`analyzer/summary.py`, `tests/test_summary.py` (add tests; keep the existing ones), a new fictional fixture `tests/fixtures/findings_sample_c.json` if you need a third session. Touch nothing else (not `report/`, not `analyzer/findings.py` unless the loader is missing a check, then say so, not `analyzer/check.py` or `analyzer/spatial.py`). Do not commit.

## Checks that prove it

1. `../../.venv/bin/python -m pytest -q` passes, offline.
2. Focused tests: two sessions sharing a place give a `cross_player` entry in both files with `here` true only for the own file and `of` 2; a place seen in one session only is absent; one session alone gives no field; a stale field is removed; `worst_t` picks the longest span; `label` falls back to the session id; the output loads through `findings.load` and renders through `report.render.render_html` (the page shows "Across players" with the right chips); idempotence.
3. Run the CLI on copies of the two sample fixtures under `../../runs/redesign/` (never on the fixtures themselves), show the resulting block and render one file to `../../runs/redesign/page-cross.html`; report its size.
4. A grep of your diff finds no em dash, no spaced en dash, no key and no path of this machine.

## Done means and report

Tests pass, CLI works, the page shows the section from the written file. Report in at most 15 lines: files, commands with exit codes, evidence paths, what you did not check, and any inconsistency you found in this brief (say so, do not silently change it).

## What came back (2026-10-28)

DeepSeek finished before Claude's limit cut the orchestrator off. No orchestrator edit to the code. The backup orchestrator reran `pytest -q` with the macOS `say` clip deselected: 147 passed. Evidence: `runs/redesign/page-cross.html`. A browser check showed "Across players", "2 of 2 players were confused here.", and the chip link to `#m1`. Fresh Grok review: PASS, no blocking findings and no nits (`docs/reviews/10-cross-player-grok.md`). Merged on main.
