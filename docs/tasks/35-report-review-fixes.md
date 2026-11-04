# 35: Fix the report after reviews 20 and 22

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-01. Implementer: Claude Fable 5.1 (it designed the page in task 32). Reviewers after: a fresh Grok 4.7 xhigh (code) and a fresh Claude Sonnet 5.5 (captures), round 2. Base commit: `eafbf73` on `main`.

Read first: `docs/tasks/32-report-design-pass.md` (the open problem and Sasha's words), `docs/design/UX_PASS.md` (the design), `docs/reviews/20-report-build-design-grok.md` and `docs/reviews/22-report-look-sonnet.md` (the findings). Follow `.claude/skills/change-analyzer/SKILL.md` for the analyzer part and `.claude/skills/validate-change/SKILL.md` before you call it done.

## Sasha's answers since task 32 (DECISIONS.md, 2026-11-01)

"agree with fables answers on its questiosn": the time-stuck rule and "Time stuck or blocked" stay; "unplanned" stays; for the video he switches to "Unplanned only" first; the strong trail stays at 30 s; the clip row under the floors stays. "expected" in place of "by design" is not decided: do not change that word.

## Fix (every item is a real finding; name the class and fix every instance)

Blocking:
1. **The heat map view must turn the timeline view off** (review 20, blocking; review 22, defect 7). The rule at `report/render.py` (`.pane:has(.view-heat:checked) :is(.timeline, ...)`) cannot reach `section.timeline`, which sits outside the pane. In the heat view the timeline bar is hidden and cannot switch the view back. Add a test that fails on today's markup.
2. **One current moment while a jump scrolls** (review 22, B1). Picking a problem (or a dropped candidate) smooth-scrolls past other cards, and the scroll sync makes them current on the way. The page's own scroll must not move "now".
3. **The stage clip follows the map time** (review 22, B2). After a scrub, or whenever the map time is outside the current moment's clip, the stage must not keep showing an older moment's clip.

Before the video (review 22, smaller defects; Sasha's half-screen demo is the reason):
4. At 960 x 1080 the top problems are visible on the first screen (defect 1).
5. The overview's empty clip box (defect 2) and the thumbnail-size clip (defect 3): the clip a judge sees beside the map is large enough to read the game.
6. Event chips cut off at 960 (defect 4); the label beside the dot runs off the floor and over a pin (defect 5).
7. Overview returns the list to the top problems (defect 6).
8. A dropped candidate says it was dropped in the stage panel, and the counter is never blank (defect 8).
9. 400 px: no sideways scroll, nothing clipped (defect 9); no mid-word breaks in the side panel (defect 10).
10. Spacing between the problems and the tiles (defect 11); the tile that reads "24 24 kept, 5 dropped" (defect 12; any new wording is a proposal in `LABELS`); timeline and pin type readable in a half-screen video (defect 13).

Analyzer:
11. **Readable game event labels.** Today: "BREAK_ROOM/kitchenSink/CabinetDoor opened". Make `analyzer/spatial.py` write labels a designer reads at a glance, from the log's own values only (for example the last path segment split into words, with the first segment as the room: "Cabinet door opened (kitchen sink, Break room)"). The words are a proposal (Claude Fable 5.1); keep them next to `VERDICT`. Regenerate with `python -m analyzer.spatial` (no model call), a focused test.
12. Review 20 nits: the duplicate `_event_icon` (`report/render.py`), and `_downsample` dropping a floor change that `floor_spans` keeps (keep a sample where the floor changes).

Not in scope: review 22's defect 14 (two Play buttons) and 15 (the long full run; Sasha answered it).

## Done means

- `.venv/bin/python -m pytest -q` passes offline, with new tests for items 1, 11 and 12.
- Both Player 1 pages regenerated; the findings comparison prints 0 differences in every protected field (id, kind, times, summary, quote, game_state, rank, beat, check verdict, note, friction, resolved) for 29 and 47 findings.
- Playwright flows in **both WebKit and Chromium** (`PLAYWRIGHT_BROWSERS_PATH=0`, `.venv/bin/python -I`): reproduce B1, B2 and the heat-view bug before the fix and show them gone after; captures at 1920 x 1080, 1440 x 900, 960 x 1080 and 400 px, light and dark; drive the Open page's flows too.
- `docs/design/UX_PASS.md` gets a short "Task 35" section: what changed, new strings.

## Rules

- Files you may change: `report/render.py`, `analyzer/spatial.py`, `analyzer/findings.py`, `tests/**`, `docs/design/**`. Not `game/`, `godot/`, the prompts, `merge_same_moment`, README, DECISIONS, STATUS or AGENTS.
- Do not call any t3-code tools. Never run rm. Do not commit. No model calls, no network, no Keychain. Never copy anything from `runs/` or `recordings/` into a tracked file.
- Build and test each step before the next one.
