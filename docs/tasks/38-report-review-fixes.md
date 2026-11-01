# 38: Fix the report after reviews 23 and 24, and raise the UX score

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-01. Implementer: Claude Fable 5.1 (it built task 37). Reviewers after: a fresh Grok 4.7 xhigh (code, round 2) and a fresh Claude Sonnet 5.5 (UX score, round 2). Base commit: `17a9675` on `main` plus the two review reports.

Read first: `docs/tasks/37-report-build-mix.md` (Sasha's decision, the layout, "What great means here"), `docs/reviews/23-report-mix-grok.md` and `docs/reviews/24-report-mix-ux-sonnet.md` (every finding with evidence). Follow `.claude/skills/validate-change/SKILL.md` before you call it done. Sasha's words for this round (2026-11-01): "rereview, fix if anything, score is ux and iterate so it is great entry."

## Fix (name the class of each finding and fix every instance of it)

Blocking:
1. **Pins take the wrong click** (review 23, blocking): the focus ring, hollow pins' empty centres, the route and the player dot are in the pointer path, so a pin opens a neighbour's moment or nothing. Fix on both maps.
2. **Play/Pause is unreadable** (review 24, defect 1): `.bar .nav button` overrides `.primary`. The main control must read clearly in every state, both themes.

Review 24, defects 2 to 11:
3. Space right after opening Watch must play or pause, never close it.
4. Back and Escape return to where the reader came from: a top problem, a badge or a map pin restores that position and focus; a still in the list returns to the list (as today).
5. His demo session: the top problem's pin (the Laboratory, another scene, at the Lobby map's edge) is half off the map, and Watch's line above the map names "Archive" while the caption says "Laboratory". A moment outside the drawn map must be visible and say so (an edge marker and a plain line), never a room that contradicts the caption.
6. The faint whole route is the heaviest ink on the map: make it recede (no dark case on the whole route; keep the 30 s trail loud), and check that small pins and hollow dropped pins still read.
7. The Open page and the Spark page look the same above the fold: one line under the session name naming the model the file holds (the words are a proposal in `LABELS`).
8. Dropped candidates: "{n} dropped" on the first screen links to the Dropped section (a scroll, not Watch).
9. While walking between moments, the left column is empty and the overlay sits on the clip's own controls: use the column for "Up next" (the next stop's still frame, its quote and its likely cause) and hide the native controls while travelling.
10. A stale walk frame when a walk restarts (draw at once in `startTravel`).
11. Next from a dropped candidate: make the change of list visible (the counter or a hint), or keep Next inside the list the reader is in; say which and why.
12. 400 px Watch: the timeline labels must not collide.

Review 23, smaller:
13. A floor change inside the 30 s window must start a new trail segment, not delete the earlier part.
14. The line above the map always shows the latest game event at or before the map time.
15. The header and dropped counts print `summary.kept` and `summary.dropped` when the summary is present.
16. "F9", "attempt", "moment" and any other visible word go through `LABELS`.
17. `ended`, `pause` and `timeupdate` act only for the clip `showMoment` loaded.

## Done means

- `.venv/bin/python -m pytest -q` passes offline, with focused tests for items 1, 2, 13, 14, 15 and 16 that fail on `17a9675`.
- A Playwright probe in **WebKit and Chromium** (`PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I <script>`) that really clicks: every pin on both floors of her Spark overview, including the close pair 4 and 17 and the hollow dropped pins, opens its own moment; pins under the player in Watch open theirs; Space after opening Watch keeps Watch open and toggles play; Back from a top problem lands at the top problems; the Play/Pause text contrast is at least 4.5:1 in both themes. Log the results.
- The four pages in `runs/final/` re-rendered (`.venv/bin/python -m report.render <findings> -o <page>`), no console errors in either engine.
- Captures in `/tmp/t38/shots/` for the same sizes and states as task 37, plus his first screen and his top problem in Watch at 1920 x 1080 and 960 x 1080, and the walking state at 1920 and 960. A new `/tmp/t38/flow.webm` (about 30 s, her page).
- `docs/design/UX_PASS.md`: a short "Task 38" section (what changed, new strings).

## Rules

- Files you may change: `report/render.py`, `tests/**`, `docs/design/**` (and `analyzer/spatial.py`, `analyzer/findings.py` only if a fix needs data from the analyzer, with a test). Not the prompts, `analyzer/check.py`, `game/`, `godot/`, README, DECISIONS, STATUS or AGENTS, and not the review reports.
- Work in the main checkout. Do not commit. Do not call any t3-code tools. Never run rm. No model calls, no network, no Keychain. Only stop processes you started, never by name. Never copy anything from `runs/` or `recordings/` into a tracked file. No em dashes and no spaced en dashes. "by design" stays.

## Report (short)

Files changed; for each numbered item, fixed or not and the evidence; commands and results; capture and flow paths; new strings; what you did not check.
