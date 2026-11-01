# 37: Build the chosen report layout (the mix)

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-01. Implementer: Claude Fable 5.1 (it designed the watch-read mock in task 36). Reviewers after: a fresh Grok 4.7 xhigh (code) and a fresh Claude Sonnet 5.5 (UX, with a score); then fix and review again until the UX is great. Base commit: the commit that adds this file on `main`.

Follow `.claude/skills/change-analyzer/SKILL.md` if you touch the analyzer, and `.claude/skills/validate-change/SKILL.md` before you call it done. Load the design skills your session lists (`design:design-critique`, `design:ux-copy`, `design:accessibility-review`, `dataviz`) and use them.

## Sasha's decision (DECISIONS.md, 2026-11-01, verbatim)

"I agree with all, go mix, build it fully and properly, rereview, fix if anything, score is ux and iterate so it is great entry."

"all" is this recommendation, which he accepted as written:

- **Base: watch-read** (`runs/check/mock36/watch-read/`: `render_mock.py`, `her.html`, `NOTES.md`, `shots/`). Two modes, never both on screen: Read, a calm page to scroll (top problems, then every moment with a still frame, the dropped candidates in their own quiet section); Watch, the player (the clip about two thirds, the map about one third, a slim timeline), opened by any moment or by Play. Back or Escape returns to the same place in Read.
- **From scroll-snap** (`runs/check/mock36/scroll-snap/`): the map beside the top problems on Read's first screen (pins, the whole route faint, the counts as its legend), so the level is visible at once; and the player's quote as each moment's headline in Watch, with the summary and the "Likely cause" line under it.
- **From one-screen** (`runs/check/mock36/one-screen/`): the line above the map with the room, the floor and the last game event; and "Up next" (the coming moment's line) while the session plays.
- **Kept from watch-read:** "Before this moment" (the game events just before), Back and Escape to the same place, Previous and Next at the top, the map growing to two thirds while the session walks between moments and the clip taking over at a moment.
- **The five answers:**
  1. The heat map is a "time spent" switch on the first-screen map only.
  2. Play the session stops only at unplanned moments (friction stuck or blocked); it passes by-design moments without stopping, and Previous and Next reach every moment.
  3. The strong trail is fixed at 30 s, with the whole route faint behind it.
  4. One floor at a time, following the player; the other one click away.
  5. Area, Puzzle, Attempt stay as place headings in the Read list.

Earlier, still in force: "by design" is his decided word (2026-11-01: "as for 2 lets leave by design, it is commonly used thing."). "unplanned" stays. "Time stuck or blocked" stays (the union of visit and attempt spans of stuck or blocked moments). The video plan: "one moment, one drop, the map, then Open beside it", with the Open page beside the Spark page at about 960 x 1080 each.

## What "great" means here (the UX bar the reviewer will score)

A level designer who opens the page cold, with no instructions:
1. knows in a few seconds what went wrong and where (verdict, top problems, map);
2. gets from a problem to its clip in one click, and back in one;
3. at a moment sees one big clip, the player's words, the likely cause, and where the player is and was, with nothing repeated;
4. can play the session and always understands what is happening between moments;
5. finds a dropped candidate and its reason without hunting;
6. never wonders which mode they are in;
7. and the same holds at half a screen (960 x 1080) and on a phone (400 px, reading only is fine).

## Build

- **Replace `report/render.py`** with the mix. Keep its entry points as they are (`render.main(argv)` for `analyzer/analyze.py` and the CLI, `render_html(data)` for the tests). One path: delete everything the new page no longer uses (the side panel, the clip row, the chips, the two-floors-side-by-side view, the toolbars, the trail select, the "Unplanned only" switch, the separate heat view) and their LABELS. No dead code.
- **The file is the single truth.** The page computes nothing that is a finding, a time, a position or a count. Pixel mapping, layout, which moment is current, playback timing, the still frame's seek (`#t=`) and lookups by time (the room, the floor, the events before a time) stay on the page. If something must come from the analyzer, add it in `analyzer/spatial.py` with a focused test and the schema check in `analyzer/findings.py`, and regenerate with `python -m analyzer.spatial` (no model call).
- **Words:** every visible string lives in `LABELS`. Reuse today's wording where it fits; mark each new one "Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording" and list it in your notes. The "Likely cause" label is an existing proposal. English. No em dashes and no spaced en dashes anywhere.
- Kinds never color alone (stuck square, confused circle, surprised diamond, suspected bug triangle). Light and dark (`prefers-color-scheme`), `prefers-reduced-motion`, keyboard (left and right, Space, Escape, Enter), focus visible, every string escaped, a page that still reads without script. No libraries, no network: one self-contained HTML file plus its clip folder.
- `#m<rank>` and `#d-<id>` links keep working (they open that moment in Watch).

## Inputs (private sessions, git-ignored: never copy any of them into a tracked file)

Final findings with the new check prompt (v2 with the friction guard, commit `6c4953c`), in `runs/final/`:
- `cogito_person2-muse-spark-1.2-contributor-findings.json` (hers, Spark; the busy one) and `cogito_person2-meta-models-muse-spark-open-1026-findings.json` (hers, Open);
- `cogito-muse-spark-1.2-contributor-findings.json` (his, Spark; the demo and the GIF) and `cogito-meta-models-muse-spark-open-1026-findings.json` (his, Open).
Render with `.venv/bin/python -m report.render <findings.json> --out <page.html>` (check `report/render.py --help` for the exact flags) into `runs/final/`. Maps: `report/maps/`. The mocks' renderers show how each piece was drawn; copy what you need.

## Done means

- `.venv/bin/python -m pytest -q` passes offline. `tests/test_report.py` is rewritten for the new page where it tested the old layout, keeping the invariants (escaping, the page shows the file, kinds by shape, labels from `LABELS`, the anchors), with focused tests for the new rules (Play stops only at unplanned moments, one floor shown, the heat switch only on the overview map, no clip twice).
- The four pages render from `runs/final/`, with no console errors in WebKit and Chromium (`PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I <script>`; never `playwright install`).
- Captures of her Spark page in `/tmp/t37/shots/`: 1920 x 1080 dark and light, 1440 x 900 light, 960 x 1080 dark, 400 px light; states: Read first screen, Read scrolled to the moments, Watch at a moment mid-clip, Watch between moments while playing, a dropped candidate, the time-spent switch on. His page: first screen and one moment at 1920 x 1080 dark and 960 x 1080 dark. The Open pages: first screen and one moment.
- A Playwright flow recording `/tmp/t37/flow.webm` (about 30 s, 1920 x 1080, her page) of the seven points under "What great means".
- `docs/design/UX_PASS.md` gets a short "Task 37" section: what the page is now, new strings, what the analyzer supplies, what you did not check.

## Rules

- Files you may change: `report/render.py`, `analyzer/spatial.py`, `analyzer/findings.py`, `tests/**`, `docs/design/**`. Not the prompts, `analyzer/check.py`, `merge_same_moment`, `game/`, `godot/`, README, DECISIONS, STATUS or AGENTS.
- Work in the main checkout; nobody else edits these files while you work. Do not commit. Do not call any t3-code tools. Never run rm. No model calls, no network, no Keychain. Only stop processes you started, never by name. Never copy anything from `runs/` or `recordings/` into a tracked file.
- Build and test each step before the next one.

## Report (short)

Files changed; the commands and their results; the capture and flow paths; new strings; what the analyzer supplies now; what you did not check.

## What came back (2026-11-01)

- **Build** (Claude Fable 5.1, `17a9675`): `report/render.py` rewritten as the mix, 2451 to 1694 lines; the analyzer needed nothing new. Reviews 23 (Grok, code) and 24 (Sonnet, UX 7.4): NOT PASS (pins took the wrong click, Play unreadable, Space closed Watch, Back to the wrong place, the demo's top pin off the map).
- **Fixes** (Fable, task 38, `952ecb1`): every finding, plus "Up next" while walking, the model line, the dropped link. Reviews 25 (code PASS) and 26 (UX 8.6, the phone caption).
- **Small fixes** (Claude Opus 5.5, `a84618f`, `b24db37`): the place line follows the moment, Previous and Next off at the ends, the phone stacks in normal flow, the caption fits on laptops, each event shows once. Reviews 27, 28 (UX 8.4, the phone overlap, fixed in `b24db37`), 29 (**UX 8.9, PASS**) and 30 (code PASS).
- **Tried and reverted:** a half-screen rearrangement (`5d7400a`, review 31 NOT PASS: it cut windows 800 px high or less). The page at `f397f7e` is `b24db37` without one CSS rule that never applied.
- **Known, not fixed:** at 960 x 1080 about 300 px under the caption is empty (the map is width-limited); timeline pins pile up on a phone; the model line is easy to miss (the words are Sasha's).
