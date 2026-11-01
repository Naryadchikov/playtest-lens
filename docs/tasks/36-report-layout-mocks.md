# 36: The report layout, three new mocks

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-01. Designers: three Claude Fable 5.1 subagents in parallel, one direction each (Sasha asked for Fable). Sasha picks one, or a mix; the orchestrator then builds it into `report/render.py`, with a fresh Grok 4.7 review of the code and a fresh Claude Sonnet 5.5 review of the captures. Base commit: the commit that adds this file on `main`.

## Why (Sasha's words, verbatim, T3 Code chat, 2026-11-01; DECISIONS.md holds them)

He looked at today's page (`runs/demo-site/site/index.html#m1`, his own session; his screenshot is a T3 Code chat attachment, not in the repo) and said:

- "lets iterate on the layout more, ask fable to improve redability and remove not needed elemnts, it is too busy now. as I said, dont hesitate to pivot on some desitions and make things from sratch, I think we are ok to do couple of new mocks and choose the best UX wise."
- "also I think once the reviewed beat is reached on timeline, the most important thing on the screen should be the video, and it should be in one place, not in 2 as it is now, then map should be the second prio thing, kinda like 2/3 of the screen is video with players quote and possible problem, another 1/3 is the map with the context around seing where the player is, what was doing before, etc. and maybe lower side still can be timeline."
- "then there should be a mode just to scroll I guess, or maybe it is merged. but overall once timeline is being played I want to see only improtant things without duplicates and repetition. UX should be clean and easy, people should not spend time on onboarding the thing. load necesery skills like claude design to do revamp of the report page."
- "as for 2 lets leave by design, it is commonly used thing." ("by design" stays: that word is decided.)

"kinda like 2/3" is a guide, not a number. "maybe" on the timeline at the bottom is open. Whether scrolling is its own mode or merged is open: the three directions below answer it three ways.

## What is busy today (the orchestrator's read of his screenshot; a proposal, check it yourself)

At moment 1 on a 1920 x 1080 screen, the same moment shows three times: the card in the list (summary, quote, Game, Checker, meter, Resolved, its clip), the side panel (the same summary, quote, Game, Checker, meter) and the clip again under the floors. Around them: ten event chips, cut off; two floors side by side while the player is on one (the other mostly dark); two toggle groups; four transport buttons and "Moment 1 of 7"; a five-row timeline; the counts tile and the kind legend. Nothing tells a first-time reader where to look.

## The design problem

**At a moment, the clip is the one big thing (about two thirds), with the player's words and the possible problem beside or under it; the map is the second thing (about one third), showing where the player is and what they did just before; nothing appears twice. A designer opening the page cold knows what to do without reading instructions.**

Open questions for your direction to answer:
- **Between moments.** The page has only the moments' clips (about 20 s each, 1280 x 720), not the whole session video. When the session plays and no moment is on, what fills the video's two thirds? (The map growing, the last clip's frame, the next moment coming up, something else.) If your design wants the whole session as one compressed video, say so in your notes; build with clips only.
- **Half a screen.** The video puts the Open page beside the Spark page: two windows at about 960 x 1080. Show how two thirds and one third become a layout that still reads there.
- **What to cut.** Today's elements may go, move one step away (hover, a click, a drawer) or merge. List each one with where its information went.

## Your direction (each designer gets one; deviate if you find better, and say why)

1. **one-screen: the page is the player.** No list of cards. Before you press anything, the video's place holds the verdict and the top problems; picking one, or Play, starts. At a moment: the clip big, the words and problem with it, the map with the trail of what came before. The timeline under them is the way to move (moments as pins, dropped candidates quieter), with Previous and Next.
2. **watch-read: two modes, never both on screen.** Read is a calm document to scroll: the verdict, the top problems, then the moments in order, short (a still frame at most, no playing clips), the dropped candidates in their own quiet section. Watch is the player (clip big, map, timeline), opened by clicking any moment or Play; Escape or Back returns to the same place in Read.
3. **scroll-snap: scrolling is the timeline.** One page where each moment fills the screen (the clip big with its words and problem, the map with context), and scrolling or the arrow keys snap to the next moment. The first screen is the overview (verdict, top problems). A slim timeline is fixed at the bottom and follows. Play steps through the moments by itself; between moments the map shows the path walked.

## Fixed points

- **Every kept moment stays reachable,** with what the file holds: kind, time, rank, summary, quote, friction (shown as "by design" or "unplanned"), severity, resolved, the checker's note and the game state (these two may be one step away).
- **The dropped candidates stay reachable with their reasons.** Sasha's video structure is "one moment, one drop, the map, then Open beside it", so a dropped candidate must be easy to show.
- **Also reachable:** the top problems (`summary.problems`), the verdict and counts, both floors (the current floor at least; the other one step away), the route and the player's dot during a clip (map time = `clip.start_s + video.currentTime`), Play the session, the pipeline line ("pipeline shown on the page" is decided; where it sits is yours). The heat map and "Unplanned only" may stay, move or go: say which, and if you drop one, put it as a question for Sasha.
- **Earlier decisions you may pivot on** (Sasha allowed it for these mocks): the clip row under the floors, both floors side by side, the side panel, the event chips, trail windows, the five timeline rows, grouping by Area, Puzzle, Attempt, the heat map as its own view that turns the timeline off, the map opening on the whole route. List every one you drop in your notes, as a question for him.
- **The file is the single truth.** Your renderer reads `findings.json` and draws it. In the mock your script may derive things; list each one so the analyzer can supply it in the build.
- **Words.** "by design" stays. Reuse today's wording in `LABELS` (`report/render.py`) where it fits; every new visible word is a proposal: list them. English. No em dashes and no spaced en dashes anywhere.
- Kinds are never color alone (stuck square, confused circle, surprised diamond, suspected bug triangle). Light and dark (`prefers-color-scheme`), `prefers-reduced-motion`, keyboard reachable, every string escaped. No libraries, no network: one self-contained HTML file plus the clip folder.

## Inputs (private sessions, git-ignored: never copy any of them into a tracked file)

- **Hers (primary, the busy one):** `runs/check/person2-findings.json` (Contributor Spark 1.2; 21:21, 24 kept, 5 dropped, two floors). Clip paths in it are relative to `runs/check/`. Today's page: `runs/check/person2-report.html`. Open mode: `runs/check/person2-findings-open.json` (33 kept).
- **His (the demo):** `runs/demo-site/cogito-muse-spark-1.2-contributor-findings.json` (8:32, 7 kept, 9 dropped). Clip paths relative to `runs/demo-site/`. Today's page: `runs/demo-site/site/index.html`.
- **Maps:** `report/maps/lobby.png` and `.json` (ground) and `lobby_upper.png` and `.json` (upper floor, `y_floor_min`); `report/render.py` (`_load_floors`, `world_to_px`) shows the mapping. The findings file's `route` holds `maps`, `points` (`[t, x, z, floor]`), `heat`, `floor_spans`; it also holds `zones`, `events` (readable labels) and `summary.problems`.
- Design notes so far: `docs/design/UX_PASS.md` (Fable's task 32 pass), `docs/design/DESIGN_NOTES.md` (tokens).

## Skills

With the Skill tool, if your session lists them: `design:design-critique` on today's page first (a few lines in your notes), `dataviz` for the timeline and map marks, `design:ux-copy` for any new words, `design:accessibility-review` at the end. Say which ones were not available.

## Deliverables, in `runs/check/mock36/<your direction>/` (git-ignored)

- `render_mock.py`: `.venv/bin/python -I runs/check/mock36/<dir>/render_mock.py <findings.json> <out.html>`, standard library only, reading only the findings file and `report/maps/`, writing clip `src` paths relative from the output page. You may copy from `report/render.py`. Written so the chosen one can become `report/render.py`.
- `her.html`, `her-open.html`, `his.html`, rendered with it.
- `shots/`: 1920 x 1080 dark and light, 960 x 1080 dark, 1440 x 900 light; the states: first screen, a moment with its clip playing mid-clip, a dropped candidate, Play the session midway. Her page for all; his page at 1920 x 1080 dark for the first screen and one moment.
- `flow.webm`: a Playwright recording of about 30 s at 1920 x 1080 on her page: open, pick the top problem, its clip plays, the next moment, Play the session for a few seconds.
- `NOTES.md`, short: the direction in two lines; your critique of today's page; what you cut and where each piece of information went; earlier decisions you dropped, as questions for Sasha; new words; what the analyzer would have to supply; what you did not check.

## Rules

- Write only in your own folder and in `/tmp/mock36-<your direction>/`. Do not edit any other file in the repo. Do not commit.
- Do not call any t3-code tools. Never run rm. No model calls, no network, no Keychain.
- Playwright: `PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I <script>` with WebKit and Chromium (both play the H.264 clips; headless Firefox can't). Never run `playwright install`. Pages open from `file://`, no server. Only stop processes you started, never by name.
- Build and look at each step before the next. A clickable prototype on real data is the goal; spend the polish where a judge's eye goes.

## Report (short)

The folder; the three pages; the shots and `flow.webm`; the notes' headings in one line each; what you did not check.

## What came back (2026-11-01)

All three delivered in `runs/check/mock36/<direction>/`: `render_mock.py`, her Spark and Open pages and his, shots in Chromium and WebKit, a 30 s `flow.webm`, `NOTES.md`. All three converged on the same moment screen (the clip about two thirds with the words under it, one floor with the trail and the events just before, a slim timeline) and differ in how you move: one-screen has no list, watch-read has a calm list and a player, scroll-snap snaps one moment per screen. All three dropped the heat map, "Unplanned only", the trail select and the side-by-side floors, and listed them as questions. Skills: design-critique, accessibility-review in all three; dataviz and ux-copy in two (the palette validator needs node, not installed).

Sasha's side-by-side page: `runs/check/mock36/compare.html` (copy my picks). The orchestrator's recommendation (Claude Opus 5.5): watch-read as the base, with scroll-snap's overview map and quote headline and one-screen's context line.
