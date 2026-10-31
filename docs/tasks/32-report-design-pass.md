# 32: The final design and UX pass on the report

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Designer and implementer: Claude Fable 5.1, a Claude Code subagent (Sasha's pick). Reviewer: a fresh Grok 4.7 xhigh (code), then a fresh Claude Sonnet 5.5 (captures). Base commit: `c1cd19c` on `main` (task 30 built: the page you start from is `runs/check/person2-report.html`; its screenshots are in `/tmp/t30/shots/`).

Follow `.claude/skills/change-analyzer/SKILL.md` if you touch the analyzer, and `.claude/skills/validate-change/SKILL.md` before you call it done.

## The open problem

**Make the session report something a level designer opens cold and understands in ten seconds, can work through without ever losing their place, and learns something from; and make it the strongest thing a hackathon judge sees in a three-minute video.**

Concretely, a designer who opens the page should know, without reading instructions:
1. What went wrong in this session, worst first, and where in the level.
2. Where to start, and what to click.
3. At every moment: which moment they are on, when it happened, where the player was (which floor, which room), what the player said, and what the clip shows. The map, the clip, the timeline and the list always agree on one current moment or time.
4. How to get from any problem to its clip and its spot on the map in one click, and back to the overview in one more.
5. That the AI's claims were checked: a second pass kept or dropped every candidate with evidence, quotes come from a transcript, and the dropped ones are listed with their reasons.

And a judge watching the video should see, in a few seconds each: the map with two floors and the route, a clip playing beside the map with the player's dot moving, the timeline filling as the session plays, the worst problems at the top, a dropped candidate with its reason.

Nobody has solved this yet: the three mockups each solved part of it and each has too many controls at once. Solve it your way. You may restructure the page; the constraints below are the only fixed points.

## What Sasha said (his words, verbatim; DECISIONS.md holds the dates and channels)

- 2026-10-31: "better to polish the report, dont hesitate to redesign it completely if you think it is better, I think bigger map with 2 levels is the better thing, maybe more dynamic events on the page and would be nice if you see both the map and the clip with the bit along side somehow, dont hesitate to run couple of ideas and pick the best."
- 2026-10-31: "as for the mockup, I overall like the timeline ideas from A, but UX should be good and easy to follow, designer who reviews the thing shold not be lost there."
- 2026-10-31: "I think it worth to run Fable 5.1 as well as subegent to do final design improvements and UX suggestions"
- 2026-10-31: "on the design report side, merge my thoughts with your best suggestions out of three earlier done mockups, and state the open problem for fable to solve, on making the report easy to use, insightful and strong for hackaton submition"
- 2026-10-30, on the content of the current Spark page: "overall I like Spark report, feels that everything is on point." and Spark "was a bit easier to read".
- 2026-10-31, a block of the worst problems at the top: "yes". Showing the pipeline on the page: "do it" (the wording is his to decide).
- 2026-10-28, on the old map: "a bit too messy and not really readable", "it is almost impossible to follow the route of the player since things are just overlapping"; he wanted "some timeline or filtering" and "having timeline and scroll and see things appear"; "so it looks more polished and we have only needed and relevant informaton at a time"; trail windows "from X-Y to X, where Y can be 10 sec, 15, 30, etc."; "heat map should be turning off the timeline view, and just be the heat map, check how Bf and COD heatmaps look like that are publically avalible."
- 2026-10-28, decided: the hierarchy is Area, Puzzle, Attempt; the map opens on the whole route.

## What the orchestrator took from the three mockups (proposals by Claude Opus 5.5)

The mockups are in `runs/design/mockup-a.html`, `-b.html`, `-c.html` (git-ignored; screenshots in `/tmp/a-shots/`, `/tmp/b-shots/`, `/tmp/c-shots/`). Task 30 built B's structure with parts of C into `report/render.py`. Worth keeping or bringing in:

- **From A (Sasha liked its timeline):** one hero screen with the two floors, a moment panel and a full-width timeline under them; timeline rows for rooms, the upper floor, moments, dropped candidates and game events; a draggable playhead; Play that can stop at each moment and play its clip at normal speed, then go on; game events appearing beside the player's dot as they happen; an opening panel with the verdict and a big "Play the session"; Previous, Next and Overview in the panel; the picked clip's stretch drawn on the route.
- **From B (the build's base):** the list drives the map as you scroll; the moment's visit or attempt drawn strong over a faint full route; its floor outlined, the other dimmed; every moment's clip beside its text in the list; the game events near the moment; the page still reads as a document without script.
- **From C:** rank numbers on the timeline markers; zoom to a span and "Zoom to moment"; hover details; Space, left and right arrows, Enter; the clip's own 20-second strip of events under the video; future moments dimmed, not hidden.

What went wrong in all three, the orchestrator's read:
- **Too many controls at once:** speed, trail windows, two views, a clip checkbox, zoom, keyboard hints, all visible on the first screen. The first screen needs one obvious action, with the rest one step away.
- **No answer to "where do I start".** The problems block (task 30 adds `summary.problems`) is the natural start: each problem should lead straight to its moments on the map and the clip.
- **The signal is diluted.** Of 24 kept moments on her session, 16 are low-friction "by design" learning moments; 8 are real friction (`check.friction` stuck or blocked). Every moment stays on the page, but the hierarchy should make the 8 stand out and let the 16 recede, and a filter between them is fair game.
- **Competing interaction models.** Scroll sync, session playback, timeline scrub and clip playback each move "now". Pick one spine (time, or the current moment) that everything follows, and make it visible.
- **Raw game event labels** ("BATHROOM_STALL2 unlocked") read as noise next to the player's words. Present them so they help (quiet, grouped, iconified, on hover), or say what the analyzer should supply instead.
- **"Time lost" misleads.** `summary.lost_s` and each problem's `lost_s` count only the length of merged moments (`end_s` minus `time_s`); a single moment counts zero. On her session all 3:24 lands on the Break Room (two merged moments) and the Code Lock's three attempts count 0:00, so the Break Room ranks above the Code Lock. The rule is a proposal, never Sasha's. Propose a fairer measure (for example the attempt or visit spans the file already holds) or drop the number from the ranking; implement it in the analyzer only if it is clearly better, and put the choice to Sasha as a question either way.
- **Task 30 removed some of today's page** to follow mockup B: the card dimming and its span note, and the pin list; every group is open. Bring back what a designer misses.
- **The demo needs half a screen.** The video puts the Open page beside the Spark page: two browser windows side by side on 1920 x 1080, so each page must still read at about 960 x 1080. There is no blended third report (Sasha, 2026-10-30).

## Fixed points

- **Content:** the findings, their kinds, summaries, quotes, times, ranks, check notes, friction and resolved status are what the file holds; nothing is rewritten or hidden for good. Today's grouping and section order stay (`_render_groups`); you may suggest a better order in your notes, not implement it.
- **The file is the single truth.** The page computes nothing that is a finding, a time, a position or a count. Pixel mapping, layout, stacking marks, which moment is current, and playback timing stay on the page. If the design needs new data, add it in `analyzer/spatial.py` with a focused test and the schema check in `analyzer/findings.py`, and regenerate with `python -m analyzer.spatial` (no model call).
- **Words:** every visible string lives in `LABELS`, reusing today's wording where it fits; each new string is commented "Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording" and listed in your notes. "by design" is a proposal Sasha may change. English. No em dashes and no spaced en dashes anywhere.
- **Kinds are never color alone** (stuck square, confused circle, surprised diamond, suspected bug triangle). Light and dark, `prefers-reduced-motion`, keyboard reachable, every string escaped. No libraries, no network: one self-contained HTML file per session plus its clip folder.
- **The heat map is its own view** and turns the timeline view off. The map opens on the whole route.

## Tools

- Data: `runs/check/person2-findings.json` (Spark, the page to show) and `person2-findings-open.json` (Open), after task 30's regeneration; render with `.venv/bin/python -m report.render <findings> -o <page>`. The session is a tester's private recording: never copy anything from `runs/` or `recordings/` into a tracked file; fixtures stay synthetic.
- Browser: Playwright is in `.venv` with its own WebKit and Chromium; both play the H.264 clips. Set `PLAYWRIGHT_BROWSERS_PATH=0` and run scripts with `.venv/bin/python -I`. Use it to click, scroll, play clips, take screenshots at 1920 x 1080, 1440 x 900, 960 x 1080 and 400 px wide, in light and dark, and to record a short video of the main flows. Never run `playwright install`.

## Deliverables

1. The design implemented in `report/render.py` (and the analyzer, if needed), with focused tests updated or added in `tests/`.
2. `docs/design/UX_PASS.md`: the problem as you understood it; the design and why; what changed; the suggestions you did not implement and why; the new strings; numbered open questions for Sasha, each with where it comes from, why it matters and your recommendation.
3. Evidence: the test count; a comparison showing every finding's id, kind, times, summary, quote, rank, verdict, note, friction and resolved status are unchanged in the regenerated files; screenshot paths for the states above; the recorded flow video path; what you did not check.

## Rules

- Files you may change: `report/render.py`, `analyzer/spatial.py`, `analyzer/findings.py`, `tests/**`, `docs/design/**`. Not `game/`, the prompts, `merge_same_moment`, README, DECISIONS, STATUS or AGENTS.
- Do not call any t3-code tools. Never run rm. Do not commit. No model calls, no network, no Keychain.
- Build and test each step before the next one.
