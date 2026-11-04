# 30: Build the redesigned report (two floors, the map follows the moment)

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Implementer: a Claude Opus 5.5 subagent. Reviewer: a fresh Grok 4.7 xhigh (code), then a fresh Claude Sonnet 5.5 (captures). Base commit: `1cb117f` on `main`.

Follow `.claude/skills/change-analyzer/SKILL.md` and `.claude/skills/validate-change/SKILL.md`.

## Sasha's words this rests on

- T3 Code chat, 2026-10-31: "better to polish the report, dont hesitate to redesign it completely if you think it is better, I think bigger map with 2 levels is the better thing, maybe more dynamic events on the page and would be nice if you see both the map and the clip with the bit along side somehow, dont hesitate to run couple of ideas and pick the best."
- Same chat, on a block of the worst problems at the top: "yes".
- Same chat, the first task: "polish the look of the report only. Not the findings, not the prompts, not the merge." The redesign changes the page and the report data the page draws (route, floors, heat, events, a problems summary). It does not change which findings exist, their kind, summary, quote, times, verdicts, ranks or check notes, and it does not touch a prompt or `merge_same_moment`.
- DECISIONS.md, 2026-10-28: the hierarchy is Area, Puzzle, Attempt; the map opens on the whole route; the heat map is its own view and "should be turning off the timeline view, and just be the heat map"; trail windows "10 sec, 15, 30, etc.".
- Sasha said of the current Spark page: "overall I like Spark report, feels that everything is on point." Keep its content and its grouping.

## The pick (orchestrator's, from task 29)

Base: mockup B, `runs/design/mockup-b.html` (git-ignored; open it and read its script). Its screenshots: `/tmp/b-shots/`. Also read mockup C (`runs/design/mockup-c.html`, `/tmp/c-shots/`) for the parts named below.

Layout, wide screens (1440 x 900 and 1920 x 1080):
- **Left column, scrolling:** header (session, recording, length, model), the verdict, then the new **problems block**, the counts, then the **session strip**, then the moments and the dropped candidates.
- **Right pane, sticky:** a toolbar (Timeline / Heat map, Play, Trail windows, the time readout), a slider, the two floors side by side, and the **moment box** under them (the current moment, and the game events near it).
- **Scroll sync (from B):** the moment in the middle of the screen lights its pin, draws its visit or attempt strong over a faint full route, outlines its floor. A playing clip holds the map on its moment and moves the dot: map time = `clip.start_s + video.currentTime`, the dot snapped to the last route point at or before that time, on that point's floor (no interpolation).
- **Session strip:** one row per room (B), an upper-floor row, a moments row whose markers carry the rank number (C), a dropped row with hollow shapes. Clicking or dragging on the strip sets the map time.
- **Play:** runs the whole session on the map at 10x, clips off; the moment box shows the last moment passed and the game events as they pass. Left and right arrow keys step between moments (C).
- **Heat map view:** per floor, only heat on the floors; trail, pins and dot hidden.
- **Dropped candidates:** a visible section at the end with each reason (today's text), and hollow pins on the map.
- **Narrow screens** stack the pane above the column. Without script the page still shows every moment with its clip and both floors with the whole route.

Differences from mockup B, on purpose:
- **Grouping and order stay today's:** `_render_groups` in `report/render.py` (sections in time order, a puzzle groups its attempts, an area visit is its own section). Do not switch to B's area-first grouping.
- **No crop from the route.** Each floor is drawn from its own map file at its own aspect: `report/maps/lobby.png` + `lobby.json` (ground, 1334 x 2048) and `lobby_upper.png` + `lobby_upper.json` (upper, 905 x 2048, its own world box, same scale). Unvisited rooms stay on the page.
- **Remove every capture-only hook** (`#selftest`, `&shot`, `#sim`, error boxes). Plain `#m<rank>` anchors stay, as today.

## Analyzer changes (`analyzer/spatial.py`, `analyzer/findings.py`, tests)

The page computes nothing that is a finding, a time, a position or a count. Pixel mapping, stacking marks into rows and which moment is current stay on the page. Everything else comes from the file:

1. **Floors.** Group map JSONs by `scene`; a scene's floors are ordered by `y_floor_min` (missing or null is the ground floor). A position sample's floor is the highest floor whose `y_floor_min` is at or below the sample's `y` (keep `y` when collecting samples). A scene with one map file is one floor.
2. **`route`:** `{"scene", "maps": [map names in floor order], "points": [[t, x, z, floor]], "heat": [{x, z, r_m, seconds, floor}], "floor_spans": [{floor, start_s, end_s}]}`. Heat is computed per floor (the CEO Office upstairs sits over the Break Room; one spot must not mix them). Replace the old `map` string; one format, update the fixtures.
3. **`at`** gets `floor`; dropped candidates get an `at` too. The pin nudge works per floor.
4. **`zones`:** the room visits the strip draws (`beats.zone_intervals`, video time; compute them once and reuse).
5. **`events`:** game events from the log in video time, `{t, kind, label}`, for door, pickup, quest, lock, pause and resume. Labels from the log's own values (node names are rough; that is fine).
6. **`summary.problems`:** the worst places, for the problems block. Proposal by Claude Opus 5.5 (Sasha decides the rule's numbers and the words): aggregate kept findings by area and puzzle across visits (a puzzle by area plus puzzle, an area without a puzzle by area); keep places with at least one kept finding whose `check.friction` is `stuck` or `blocked`; order by worst friction (blocked, then stuck), then time lost (the same rule as `summary.lost_s`), then earliest time; at most 5. Each: `{place, moments: [ids], attempts, lost_s, friction, resolved}` where `resolved` is `solved`, `abandoned`, `mixed` or `unknown` from the kept findings' `check.resolved`.
7. Validate every new field in `analyzer/findings.py`. `python -m analyzer.spatial <findings> --log <jsonl> --video-flash-s <s>` stays the way to redo these fields on an existing file, with no model call.

## Words

Every visible string lives in `LABELS`. Reuse today's wording. Each new string carries a comment "Proposal (Claude Opus 5.5, 2026-11-01), not Sasha's wording". "by design" stays as it is. No em dashes and no spaced en dashes. List the new strings in your report.

## Regenerate (private data, git-ignored)

1. Copy `runs/check/lobby-player-1-findings.json` to `runs/check/lobby-player-1-findings-before-floors.json`, and the same for `-open`. Copy `runs/check/lobby-player-1-report.html` to `runs/check/lobby-player-1-report-polish.html`, same for `-open`.
2. Run the spatial step on both findings files (the log is `recordings/cogito/2026-10-30T12-20-05Z.jsonl`, the flash is each file's `session.start_flash_s`), then render both pages to their usual names.
3. Prove the findings did not change: a script that compares, for every finding, `id, kind, time_s, end_s, summary, quote, game_state, rank, check.verdict, check.note, check.friction, check.resolved, beat` before and after, and prints the differences (expected: none).

## Done means

- `.venv/bin/python -m pytest -q` passes offline, with the count. Focused new tests: floor assignment, per-floor heat, the problems rule, schema checks of the new fields, the page draws two floors and the problems block, `#m<rank>` anchors exist for every kept finding.
- Screenshots (headless Firefox with a throwaway profile under `/tmp`; `content-override` 0 or 1 plus `browser.theme.content-theme` and `ui.systemUsesDarkTheme` for light): 1440 x 900 dark and light, a selected moment upstairs, the heat map view, 1920 x 1080, and a narrow 400 px width. If `/Applications/Google Chrome.app` exists by then, also check a clip playing moves the dot (a throwaway `--user-data-dir` under `/tmp`; Playwright may be installed into `.venv` only, with `channel="chrome"`, never `playwright install`).
- The findings comparison prints no difference. Three random kept findings read the same in the page as in the file.

## Rules

- Files you may change: `analyzer/spatial.py`, `analyzer/findings.py`, `analyzer/check.py` only where it calls the spatial step, `report/render.py`, `tests/**`, `docs/design/DESIGN_NOTES.md`, `docs/LOG_SCHEMA.md` if a field it documents changes. Not `game/` (another author owns it today), not README, DECISIONS, STATUS, AGENTS, not the prompts, not `merge_same_moment`.
- Do not call any t3-code tools. Never run rm. Do not commit. No model calls, no network, no Keychain.
- Never copy anything from `runs/` or `recordings/` into a tracked file. Fixtures stay synthetic.

## Report (short)

Files changed; the test count; the findings comparison output; screenshot paths; the new strings; what you did not check.
