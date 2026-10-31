# The report's design and UX pass (task 32)

Designer and implementer: Claude Fable 5.1, a Claude Code subagent, 2026-11-01. Base: `c1cd19c` (task 30's build), brief in `docs/tasks/32-report-design-pass.md`. Everything here is a proposal unless it quotes Sasha; the look, the words and the numbers are his to judge.

## The problem as I understood it

A level designer opens the session page cold. In ten seconds they should know what went wrong and where, and what to click first. Then they work through the moments without ever wondering "which moment is this, when was it, where was the player, what did they say, what does the clip show". Any problem leads to its clip and its spot on the map in one click, and back in one more. And the page shows that the AI's claims were checked.

The same page is what a hackathon judge sees for a few seconds in a video, at half a 1920 x 1080 screen: two floors with the route, a clip beside the map with the player's dot moving, a timeline filling, the worst problems, a dropped candidate with its reason.

Task 30's page had the parts but three things fought each other: scroll, session playback, timeline scrub and clip playback each moved "now"; the first screen showed every control at once; and the 16 "by design" moments buried the 8 real ones.

## The design

**One spine: the current moment.** Everything on the stage is a view of one state, the current moment (or, between moments, the map time). Picking a problem, a pin, a timeline mark, a card number, Previous or Next makes a moment current. Playing the session moves the map time and makes each moment current as it reaches it. Scrolling the list makes the card in the middle current, when nothing is playing. There is no second "selected" thing anywhere.

**The stage** (the right column on wide screens, the top of the page under 1100 px):

- The two floors side by side, as tall as the viewport allows, the current floor outlined and the other dimmed.
- A side column beside the floors: in the overview, one big "Play the session" and two lines on how to start; in a moment, the moment's own words (number, time, kind, "unplanned" or "by design", place, summary, quote, game state, checker note, friction and outcome), cloned from its card so nothing is written twice; while the session plays, the map time in large type, the room and the floor, and the last moment passed. In the heat map view, the heat legend.
- A foot row under both: the current moment's clip (paused on the moment's own frame when picked, playing when the session reaches it), the game events of the moment's visit and clip as quiet chips with a small icon per kind, and one transport row: Play or Pause, Previous, Next, Overview, "Moment n of N". The trail length appears only while the session plays.
- The toolbar holds two switches only: Timeline or Heat map, and All moments or Unplanned only.

**The timeline** is a bar across the foot of the page that stays in view: the rooms on one row with their names in the bars (puzzle visits in the puzzle colour), the upper floor, the kept moments by rank (up to three rows), the dropped candidates as hollow shapes, the game events as ticks, and the axis. The current moment's visit and clip are shaded on it; the session's playhead fills it from the left as it plays. Click or drag to set the map time. Full width means the names and the marks stop overlapping, which they did in the right column.

**Playing the session** runs at 10x between moments, stops at each shown moment and plays its clip at normal speed from where the map is, then goes on. The dot moves on the map in both. A game event that just happened is written beside the dot for a moment and lit in the events row. "Unplanned only" makes the run stop at the 8 real problems instead of all 24.

**The hierarchy of moments.** Everything stays on the page. A moment by design (the check's "learning" friction) gets a smaller pin and timeline mark and a thinner card edge; an unplanned one (stuck or blocked) keeps the full size. "Unplanned only" hides the by-design moments from the map, the timeline and the list; groups with nothing left hide too.

**The document** on the left is unchanged in content and order: the verdict, the top problems (now numbered, worst first, each place a link to its first moment, each moment a rank chip), the glance tiles, across players, the moments in today's grouping, the dropped moments with their reasons. The list follows the current moment when the stage is on screen; when the stage is stacked above the list (half a screen), picking a moment brings the stage into view instead, so the demo never scrolls away from the map.

**Without script** the page is a document: the header, the problems, every floor with the whole route and pins, the legend, the timeline with its marks as links, every moment with its clip, every dropped candidate with its reason.

**Keyboard:** Space plays and pauses, left and right step between moments, Escape returns to the overview. Every pin, mark, chip and button is a link or a button.

### Why this and not the mockups' layouts

Mockup A's hero (floors, panel, full-width timeline) is the strongest first screen and Sasha liked its timeline, but it has no room for the document. Mockup B's document beside a sticky map reads well but has no place for the clip beside the map, and its right column was too narrow for a timeline. This page keeps B's two columns and puts A's stage in the right one, with the timeline where A had it: across the whole page. The map loses height to the clip row, which is the price of Sasha's "see both the map and the clip with the bit along side". On a 1920 x 1080 screen the floors are about 640 px tall; on 1440 x 900 about 500 px; at 960 x 1080 about 540 px.

## What changed

- `report/render.py`: the page grid (header, column, stage, timeline bar), the stage (floors, side column, foot row), the timeline bar, pins and marks sized by friction, the focus filter, the script rewritten around one state. Every visible string is in `LABELS`.
- `analyzer/spatial.py`: the time-stuck rule (below). Field names and the schema are unchanged.
- `tests/test_report.py` and `tests/test_spatial.py`: updated to the new structure and rule, with new focused tests (moments by design recede, each moment is written once, the timeline rows and height, the no-script legend, the time-stuck rule).

### The time-stuck rule (a proposal, question 1 below)

The old `lost_s` added up the length of merged stuck and confused moments, so a single moment counted zero and a "by design" confused moment counted as lost. On the Spark session the Break Room's 3:24 was really 2:08 of blocked searching plus 1:16 of a by-design drag-and-drop moment, and the Code Lock's three abandoned attempts counted 0:00.

The new rule: the union length of the attempt or visit spans (`beat.attempt_start_s` to `attempt_end_s`) of the kept findings whose friction is stuck or blocked; a finding with no usable span falls back to its own `time_s` to `end_s`. The tile reads "Time stuck or blocked, in the visits and attempts with an unplanned moment", and a problem reads "2:34 stuck". On the Spark session: Break Room 2:34, Code Lock 1:04, CEO Office 0:11, Lobby 1:53, total 5:42 of 21:20; the ranking is unchanged. On the Open session the Archive rises from fifth to third (0:44), the others keep their order. A visit span over-counts when the player was only briefly stuck in a long visit; the old rule under-counted to zero. Sasha may prefer a third rule or no number.

## Suggestions I did not implement

- **Game event names.** "BREAK_ROOM/kitchenSink/CabinetDoor opened" is the log's node path. The page can only quiet it (muted chips, an icon, the path cut at the chip's edge). A readable name needs the analyzer or the add-on: a display name per node, or a rule that keeps the last path segment and splits camel case ("Cabinet door opened, kitchen sink"). That belongs to the Godot side and the analyzer, outside this task's files.
- **A better order of the sections.** The brief keeps today's grouping and order. If Sasha wants a change: the dropped moments could sit right after the top problems, since "what the check threw out" is the second thing a sceptical judge looks for.
- **A pin list.** Task 30 removed the old pin list. The timeline marks with their hover labels, the problems' rank chips and the "Moment n of N" counter cover the same need; I did not bring it back.
- **Collapsed groups.** Kept open: scrolling the list is what makes a moment current, and a closed group would hide its cards from that.
- **Speed control.** Fixed at 10x between moments; a clip always plays at 1x. One fewer control.
- **An F9 row on the timeline.** This session has no F9 presses; the markers still draw on the map and link to their moment.

## New strings (all proposals, Claude Fable 5.1, 2026-11-01; Sasha decides the wording)

- Tiles: "Time stuck or blocked", "in the visits and attempts with an unplanned moment".
- Problems: "{time} stuck" (was "{time} lost").
- Focus switch: "Which moments to show" (aria), "All moments", "Unplanned only".
- Side column: "Play the session", "Runs at 10x and stops at each moment to play its clip at normal speed, then goes on. Or pick a problem, a pin or a moment.", "Space plays and pauses. Left and right arrows step between moments. Escape returns to the overview.", "Last moment: {label}".
- Transport: "Previous", "Next", "Overview" (mockup A's words), "Moment {n} of {of}".
- Events: "Game events so far", "No game events yet." ("Game events in this moment's visit and clip" and "No game events in this span." are task 30's.)
- Timeline: the aria text, "Rooms", "Events" (row labels), "{time} {label}" (an event tick's tooltip).
- Heat legend note: "... The route, the pins and the timeline are in the timeline view."
- Removed: "Scroll the moments to light each one on the map. Play runs the whole session.", "Show all moments", "Game events up to {time}", "Time in the recording", "Where the player is at the slider's time".

## Open questions for Sasha

1. **The time-stuck number.** From the brief's "time lost misleads" item. It decides the tile on the first screen and the order of the top problems. I implemented the visit-and-attempt rule above because the old one counted a real problem as zero; my recommendation is to keep it and the wording "Time stuck or blocked", and to drop the number from the ranking only if you find a visit span over-counts on more sessions.
2. **"by design" and "unplanned".** The tags come from task 23 (Claude Opus 5.5). They now also drive the pin sizes and the "Unplanned only" switch, so they carry more weight. My recommendation: keep "unplanned", and consider "expected" for the other, since "by design" claims intent the analyzer cannot know.
3. **What the session play stops at.** It stops at every shown moment (24, or 8 with "Unplanned only"), and plays each clip in full, so a full run of all 24 takes about ten minutes. My recommendation: for the video, switch to "Unplanned only" first (about five minutes), or press Next during a clip to skip ahead.
4. **The strong trail while the session plays.** 30 s by default (your "10 sec, 15, 30, etc." windows stay in the select, plus "From start"). My recommendation: 30 s; the whole route stays faint behind it so the map never fills up.
5. **The map's size.** The clip row takes about 190 px from the floors. If you would rather have the clip in the side column and the floors taller, that is a CSS change; it costs the events row and makes the clip smaller. My recommendation: keep the clip row; it is what the judge sees.

## Evidence

- Tests: `.venv/bin/python -m pytest -q` (the count is in the task report).
- Findings comparison: `/tmp/t32/compare.txt` (0 field differences in 29 and 47 findings; only `summary.lost_s` and `problems[].lost_s` change).
- Screenshots: `/tmp/t32/shots/` (1920 x 1080 dark and light, 1440 x 900 light and dark, 960 x 1080 dark, 400 px, no script, heat map, unplanned only, a dropped candidate, a clip playing).
- The flow video: `/tmp/t32/video/`.
- The flow check: `/tmp/t32/flow.log` (Playwright drives the page through play, stop, resume, keys, filter, scroll sync, scrub, a card's clip, the heat view).
