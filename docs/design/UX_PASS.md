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

## Task 35: the fixes after reviews 20 and 22

Implementer: Claude Fable 5.1, a Claude Code subagent, 2026-11-01. Brief in `docs/tasks/35-report-review-fixes.md`; the findings are in `docs/reviews/20-report-build-design-grok.md` and `docs/reviews/22-report-look-sonnet.md`. Everything here is a proposal unless it quotes Sasha.

### What changed

- **The heat map turns the timeline off.** The timeline bar is a sibling of the stage, so the old rule inside `.pane` never reached it. The switch now works from `.page`: the bar is invisible in the wide layout (its row stays, so the floors keep their size) and gone in the stacked one. A test checks that every rule hiding the timeline on the heat switch starts at an ancestor of both.
- **One current moment while a jump scrolls.** A scroll the page starts (a jump to a card, Overview's return to the top) holds the scroll sync until the scroll has ended: `scrollend` where the browser has it, otherwise 250 ms after the last scroll event, 3 s at most. The reader's own scrolling resumes the sync. The cards' 30vh scroll margin now applies only without script, so a jump centers the card exactly (a short dropped article used to land below the middle and hand "now" to the card above it).
- **The stage clip never points at a time the map does not.** The stage's clip is one of three things: in the overview, the first problem's moment paused on its own frame, captioned with the moment and playable in place (play makes that moment current and the list follows); in a moment, that moment's clip; while the session travels or after a scrub, a black box with no controls. A moment without a clip (a dropped candidate) shows the black box too.
- **Half a screen opens on the problems.** The top problems are their own grid row: beside the stage on a wide screen, as before, and above the stage when the layout stacks under 1100 px. At 960 x 1080 the four problems end at about 575 px.
- **The clip beside the map is bigger.** The foot row is a grid: the clip takes the row's full height on the left (292 x 164 px at 1920, 309 x 174 at 960, was 206 x 112), the legend or the game events sit beside it, and the transport row runs under them. The legend stays in the overview's foot beside the first problem's frame.
- **Game events.** The chips scroll when they overflow instead of being cut. The label beside the dot flips to the dot's left on the right half of a floor, so it never runs off the map. The "later" chips are a little less dimmed (0.65 instead of 0.45).
- **Overview and Escape return to the top of the page,** where the verdict and the problems are. The scroll sync's own return to the overview (scrolling above the first card) does not move the page.
- **A dropped candidate says so.** Its row carries a "Dropped by the check" tag (cloned into the stage panel), and the counter reads "Dropped n of N" instead of nothing.
- **Narrow screens.** The facts grid lets its value column shrink and wrap, cards never widen the page, and under 640 px the moment panel grows instead of scrolling inside 40vh. A long node path or identifier (24 or more characters) gets a soft break after each slash and underscore in the game and checker facts, so the side column wraps "BREAK_ROOM/kitchenSink/CabinetDoor" at its slashes instead of inside a word.
- **Spacing and type.** 24 px between the problems and the tiles. The kept tile reads "24 kept" with "5 dropped" under the label, so the number is not repeated. Timeline labels and room names are 12 and 11 px (were 11 and 10), pins are 10 percent larger with 15 percent larger numbers.
- **Readable game event labels** (`analyzer/spatial.py`). A door or lock label names the thing the designer placed, in words, and its room in parentheses: "Kitchen sink opened (Break room)", "Windowed door unlocked (Upper office CEO)", "Desk opened (Meeting room)". The words come from the node path only: the path's second segment is the thing and the first its room; underscores, camel case and digit runs become word boundaries; a short all-caps token stays an abbreviation. A quest id reads the same way ("Demo steal laptop completed"). The brief's example used the last segment ("Cabinet door opened (kitchen sink, Break room)"); the second segment reads better here because the last one is often the prefab's own part ("AnimatableBody3D", "FrontDoor", "Door").
- **Review 20's nits.** The duplicate `_event_icon` is gone. `_downsample` keeps every sample where the floor changes, so each span in `floor_spans` has a route point (3 points added on this session).

### New strings (proposals, Claude Fable 5.1, 2026-11-01; Sasha decides the wording)

- Tiles: "kept" (the note after the big number, was "{kept} kept, {dropped} dropped") and "{dropped} dropped".
- Stage: "Dropped by the check", "Dropped {n} of {of}".
- Event labels: "{label} ({room})" around Claude Opus 5.5's templates ("{name} opened", "{name} closed", "{name} locked", "{name} unlocked", "{quest} {step}"), with the names in words as above.

Not changed: "by design" (not decided), the two Play buttons (review 22's defect 14) and the length of a full run (defect 15), both out of this task's scope.

### Evidence

- Tests: `.venv/bin/python -m pytest -q`, 237 passed (224 before), no model call.
- Findings comparison: `/tmp/t35/compare.txt` (0 differences in every protected field for 29 and 47 findings; the labels and 3 route points are the only changes).
- Blocking findings before and after, both browsers: `/tmp/t35/blocking-before.txt`, `/tmp/t35/blocking-after.txt`, shots `/tmp/t35/shots/before-*` and `after-*`.
- Flows (play, stop, Escape, a problem, Next, arrows, scrub, filter, scroll by hand, a card's clip, a dropped mark, heat, Overview), both pages, both browsers: `/tmp/t35/flow-{spark,open}-{chromium,webkit}.log`, 0 fails.
- The smaller defects, both pages, both browsers: `/tmp/t35/probes-spark.txt`, `/tmp/t35/probes-open.txt`.
- Captures at 1920 x 1080, 1440 x 900, 960 x 1080 and 400 px, light and dark, Chromium and WebKit, Spark and Open: `/tmp/t35/shots/` (100 files).

## Task 37: the mix, built

Implementer: Claude Fable 5.1, a Claude Code subagent, 2026-11-01, on base commit 89abf7f. Brief in `docs/tasks/37-report-build-mix.md`; the layout is the one Sasha picked ("I agree with all, go mix, build it fully and properly"). Everything here is a proposal unless it quotes him. "by design" stays (his decided word).

### What the page is now

Two modes, never both on screen.

- **Read** is a document to scroll. The verdict, one line of counts, Play the session. Then the first screen: the top problems on the left, the level's map on the right with every moment pinned by rank (by design smaller, dropped hollow), the whole route faint, the counts per kind as the legend, a floor switch (radios) and a "Time spent" switch that lays the heat over the plan. Then Across players when a file has it, then every kept moment in time order under its place headings (Area, Puzzle, Attempt, as before) with a still frame each (the clip paused on the moment's own frame), the summary in bold, the quote, the likely cause, the friction meter and the outcome, and "Game state and the checker's note" one click away. Then the dropped candidates in their own section, each with its reason. The footer names the model and the recording.
- **Watch** is the player, opened by any still frame, a problem, a pin, a timeline mark or Play. The clip is about two thirds of the screen; under it the player's words as the headline, the summary, the likely cause, the meter and the outcome, the note one click away. The map is the other third: one floor at a time following the player (the other a click away until the player changes floor), the last 30 s strong over the whole route faint, the room, the floor and the last game event above it, "Before this moment" (the four game events up to the map time) under it. A slim timeline along the bottom: the rooms, the moments by rank, the dropped candidates hollow, the axis; a click sets the map's time. Back or Escape returns to the same place in Read with focus on the moment's still frame.
- **Play the session** runs at 10x between moments and stops only at the unplanned ones (friction stuck or blocked), passing by-design moments and dropped candidates; while it walks, the map takes two thirds, the next clip's first frame sits dimmed under the running time, "Up next: moment 16 at 14:02, Archive, Ground floor" and a progress bar, and the bar reads "Walking to the next unplanned moment". Previous, Next and the arrow keys reach every kept moment.
- `#m<rank>` and `#d-<id>` open Watch on that moment, paused; Back clears the hash. Without script the page is Read alone (every moment, every still frame, the floor and heat switches still work through CSS).

### What was cut

The side panel, the clip row, the event chips, the two floors side by side, the toolbars, the trail select, "Unplanned only", the separate heat view and its legend, the counts tiles, the header's meta list, the five-row timeline, the card's link to its pin, and their LABELS. The time-spent heat lives on the first-screen map only.

### New strings (proposals, Claude Fable 5.1, 2026-11-01; Sasha decides the wording)

- Header: "{length} recording, {kept} moments kept, {dropped} dropped." and "{time} stuck or blocked."; the hint "Runs at 10x between moments and stops at each unplanned one to play its clip. Previous and Next reach every moment."
- Overview map: "Floor" (the switch's label), "Time spent" (his answer 1 says "time spent"), "Each number is the time spent at that spot.", "{n} dropped", "{time} stuck or blocked", the alt text "Top-down plan of the level, {floor}: every moment pinned by rank, the player's whole route faint."
- Rows: "Game state and the checker's note", "Watch moment {rank}", "Watch the dropped candidate at {time}".
- Footer: "How this page was made: {model} proposed moments from the video and the transcript; each was checked against its clip and the event log, and the page shows the file that check wrote."
- Watch: "Back", "Clip" (the clip column's label), "Before this moment", "{room}, {floor}", "Between rooms", "Up next: moment {rank} at {time}, {place}", "Walking to the next unplanned moment", "End of the session", "Paused. Press Play or pick a moment.", "Space plays and pauses. Left and right arrows step between moments. Escape goes back.", the timeline's aria text, the map's alt text.
- Kept from today: "Top problems" and its sub line, "The moments" and its sub line, "Dropped moments", "{n} candidates the check did not keep", "Reason: {note}", "Dropped by the check", "Play the session", "Previous", "Next", "Play", "Pause", "Moment {n} of {of}", "Dropped {n} of {of}", "Game events so far", "No game events yet.", "Game", "Checker", "Likely cause", "No spoken comment.", "Clip {span}", "{time} stuck", "Partly resolved", "Resolved", "Resolved after {time}", "Abandoned", "by design", "unplanned", "Ground floor", "Upper floor", "Across players" and its lines, "Player pressed F9 at {time}", "F9 marker at {time}", the pin and room bar words, "Puzzle {n}: {name}", "Attempt {n} ({span})" and the group notes.

### What the analyzer supplies

Nothing new: `analyzer/spatial.py` and `analyzer/findings.py` are unchanged. The page prints the verdict, the counts, `lost_s`, the problems, the moments, the reasons, the zones, the events, the heat and the route as the file holds them. It derives only presentation: the still frame's seek (`time_s - clip.start_s` as a media fragment), the place label from `beat` (or `check.area`), the attempt and the floor name, the room at a time from `zones`, the floor at a time from the route point, the last event and the four events before a time, the next unplanned moment after a time, and world to map pixels.

### Known gaps and what I did not check

- Inside Chromium's own media control buttons (Tab twice into the clip) the browser keeps the Escape key; Tab out first, or press Back. From the clip itself and everywhere else Escape works in both engines.
- WebKit's Tab skips links (its default), so the pins and the problem places are reached by Tab only in Chromium; the still frames, the bar's buttons and the timeline marks are buttons everywhere.
- Both engines pause a clip that is seeked within its first moments after loading. The page avoids its own seek on arrival and, when a reader seeks while the session plays, resumes after the seek.
- Timeline marks are 22 px and pins about 30 px on screen, under the 44 px target, as before.
- The map is portrait, so the wider column while the session walks does not make it taller at 16:9; the clip still steps back to a third.
- Not checked: Firefox, Safari proper, VoiceOver, print, 200 percent zoom, a session with one floor or without a route (the test fixtures only), the Open pages beyond their first screen and one moment, the whole session at real speed (the probe jumped each clip to its end), the palette validator (no node here).

### Evidence

- Tests: `.venv/bin/python -m pytest -q`, 237 passed, no model call. `tests/test_report.py` is rewritten for the new page; `tests/test_spatial.py` has two page assertions updated.
- The four final pages: `runs/final/*-report.html`, rendered with `.venv/bin/python -m report.render <findings.json> -o <page.html>`; no console errors in Chromium or WebKit.
- Captures: `/tmp/t37/shots/` (her Spark page at 1920 x 1080 dark and light, 1440 x 900 light, 960 x 1080 dark in WebKit, 400 px light; states: first screen, time spent on, scrolled to the moments, a moment mid-clip, the Read page after Back, a dropped candidate, the session walking; his page first and moment at 1920 x 1080 dark and 960 x 1080 dark; the Open pages first and moment).
- Flow: `/tmp/t37/flow.webm` (about 35 s at 1920 x 1080, her page: the first screen and the time-spent switch, the top problem's clip, the floor switch, Next to a by-design moment, Escape back to the same place, a dropped candidate and its reason, Play the session walking the map and stopping at an unplanned moment).
- Probes (keyboard, focus, every kept moment by Next, the stops of Play, one floor at a time, the heat switch, deep links, three random moments read the same in Watch as in the file, no script): `/tmp/t37/a11y-chromium.log`, `/tmp/t37/a11y-webkit.log`.

## Task 38: the fixes after reviews 23 and 24

Implementer: Claude Fable 5.1, a Claude Code subagent, 2026-11-01, on base commit ded2110 (the page from 17a9675). Brief in `docs/tasks/38-report-review-fixes.md`; the findings are in `docs/reviews/23-report-mix-grok.md` and `docs/reviews/24-report-mix-ux-sonnet.md`. Everything here is a proposal unless it quotes Sasha. "by design" stays (his decided word).

### What changed

- **A pin takes its own click, and nothing else does.** Every pin's first child is a transparent disc of its own radius (`.hit`), the one thing that answers to the pointer; the focus ring, the edge mark, the whole route, the 30 s trail, the dot and the heat are `pointer-events: none`. A hollow dropped pin and a pin under a neighbour's ring now open their own moment, on the overview and in Watch (one `_render_pins` draws both).
- **Play/Pause reads.** `.bar .nav .primary` now sets the accent background and the on-accent colour itself, so the nav rule no longer sinks it. Contrast is 4.5:1 or better in both schemes and both states.
- **Space plays or pauses right after Watch opens.** Focus lands on Play, not Back. Enter and a click on Back still close.
- **Back returns to where the reader came from.** Opening remembers the scroll position and the opener. A top problem, a badge, a map pin or Play the session on the first screen gets that position and the opener's focus back; a still frame in the list, a chip or a deep link lands on the current moment's row, as before.
- **A moment outside the drawn map is visible and says so.** A pin whose point falls outside the map's pixels is clamped just inside the edge (radius plus 8 px) with a dashed edge mark, and its name ends in "outside the mapped area". In Watch, the line above the map reads "Outside the mapped area, Ground floor" whenever the player's route point is off the map, instead of a room or "Between rooms", and a dashed note under it says the moment is outside the mapped area with its pin at the edge. His demo's top problem (the Laboratory door at the Lobby map's edge) is the case; the spatial test fixture has another.
- **The whole route recedes.** No black casing under the whole route any more, the line is 5 px at 22 percent. The 30 s trail keeps its casing and its 14 px white line.
- **The model under the session name.** "Analyzed with {model}." prints the model the file holds, so the Open page and the Spark page differ above the fold.
- **"{n} dropped" is a link** to the Dropped section, in the header line and in the map's legend. It scrolls (the h2 has a scroll margin); it never opens Watch.
- **Walking between moments.** The clip's native controls hide while the session walks (the overlay no longer sits on them), and the left column previews the next stop under "Up next": its head, quote, summary and likely cause, cloned from its row. The travel frame draws at once when a walk starts, so no stale clock or stop from the earlier walk shows.
- **Previous and Next stay in the list the counter names.** From a dropped candidate they step through the dropped candidates ("Dropped 2 of 4"); from a kept moment through the kept ones. Why: the counter promises a list, and jumping lists on Next changed the counter without a hint. Back reaches the other list.
- **400 px Watch** hides every other axis label, so they never collide.
- **Review 23's smaller findings.** A floor change inside the 30 s window starts a new trail run instead of dropping the earlier points. The line above the map always shows the latest game event at or before the map time (its time says how old it is). The header and the dropped counts print `summary.kept` and `summary.dropped` when the file has a summary. "F9", "attempt", "visit", "moment" and "{n} dropped" live in `LABELS["words"]`. `timeupdate`, `seeked`, `play`, `pause` and `ended` act only when the clip element's current source is the clip `showMoment` loaded.

### New strings (proposals, Claude Fable 5.1, 2026-11-01; Sasha decides the wording)

- Header: "Analyzed with {model}."
- Pins: "{label}, outside the mapped area".
- Watch: "Outside the mapped area" (the room slot of the line above the map), "This moment is outside the mapped area. Its pin sits at the map's edge.", "Up next" (the column's heading while walking).
- Moved, not changed: "attempt", "visit", "moment", "F9" and "{n} dropped" into `LABELS["words"]`; the header line is now "{length} recording, {kept} moments kept, {dropped}." with the linked "{n} dropped" filled in.

### Evidence

- Tests: `.venv/bin/python -m pytest -q`, 245 passed, no model call. Nine new tests in `tests/test_report.py` (pins and the pointer path, the Play/Pause rule and its contrast, the off-map pin, the summary counts, the model line, the words in LABELS, the script rules for reviews 23 and 24, the narrow axis); all nine fail on the base page.
- Probe, Chromium and WebKit, 0 fails each: `/tmp/t38/probe-chromium.log`, `/tmp/t38/probe-webkit.log` (`/tmp/t38/probe.py`). It clicks all 28 overview pins on both floors of her Spark page (4 and 17, the hollow f13, f18, f26, f32 included) and the 22 Watch pins on the shown floor with moment 4 open, each opening its own moment; Space after opening keeps Watch open and toggles play; Back from a problem, a badge and a pin restores the scroll and the opener's focus, from a still the row; Play/Pause contrast 7.88:1 dark and 7.51:1 light in both states; two trail runs at 840 s; the event at 0:16 shown at 100 s; the walk's text drawn at once, controls hidden, "Up next" in the column; Next from a dropped candidate stays in the dropped list; the dropped link scrolls; his edge pin and the off-map lines; no label collisions and no overflow at 400 px; no console or page errors on the four pages.
- The four pages re-rendered in `runs/final/` with `.venv/bin/python -m report.render <findings> -o <page>`.
- Captures: `/tmp/t38/shots/` (45 files: her Spark page at 1920 x 1080 dark and light, 1440 x 900 light, 960 x 1080 dark in WebKit, 400 px light, the task 37 states; his page first, top problem in Watch and walking at 1920 x 1080 dark and 960 x 1080 dark; the Open pages first and moment). Flow: `/tmp/t38/flow.webm` (her page, about 35 s).

### What I did not check

Firefox, Safari proper, VoiceOver, print, 200 percent zoom, a real phone, the whole session at real speed, the Open pages beyond their first screen and one moment. The pin positions of the clamped case are presentation (the file's point is unchanged). The wording of the new strings is Sasha's call.
