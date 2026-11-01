Reviewer: Claude Sonnet 5.5, Claude Code via T3. Round 4 of the UX loop. Commit b24db37. UX review with a score.

I used the four pages in `runs/final/` as a first-time level designer would, in Chromium and WebKit through Playwright, from file://. Sizes: 1920 x 1080, 1536 x 864, 1440 x 900, 1366 x 768, 1280 x 720, 960 x 1080, 720, 600, 400 x 860, 390 x 700, 360 x 640, light and dark. I did the seven points as tasks, played her Spark session for about 75 s at 1920 (Chromium), 1280 (Chromium), 400 (Chromium) and 960 (WebKit), and repeated round 3's two measurements (clip over caption, caption height against scroll height) on every moment of all four pages at 1280 x 720, 1366 x 768, 960 x 1080, 400 x 860 and 360 x 640. No console or page errors and no horizontal overflow on any page, size or engine I opened. I scored from the pages, not from earlier numbers. Captures are in `/tmp/r29/shots/`, scripts in `/tmp/r29/s/`. Nothing was copied into the repo.

## Score

| # | Point | Score | Why |
|---|---|---|---|
| 1 | Knows what went wrong and where in a few seconds | 9 | Session name, model line, the count headline, "4 dropped" and "5:42 stuck or blocked", Play, five ranked problems with kind shapes and the map with pins all sit in the first screen at 1920, 1366 and 960 (`ch-her-spark-1920x1080-dark-first.png`, `ch-her-spark-960x1080-dark-first.png`). On his page the top problem is a pink triangle on the map edge with a dashed ring and the name "Laboratory" (`ch-his-spark-1920x1080-dark-first.png`). The headline counts moments and does not name the worst place; the list under it does. At 1440 x 900 the map legend falls just below the fold. |
| 2 | Problem to clip in one click, back in one | 9 | A title, a badge, a map pin and a dropped row each open Watch in one click. Escape and Back return to the opener (focus on the title, or on the moment's clip button) and the scroll position is kept, in both engines: from scrollY 0 back to 0, from 1800 to the moment's row at 1841 (Chromium) and 1881 (WebKit), and from a `#m9` deep link to the row at 2943. Cold-loading a `#d-` link leaves focus on the body while Watch is open (low defect 4). |
| 3 | At a moment: big clip, words, cause, where, nothing repeated | 9 | The order is clip, status line, the quote as headline, the summary, "Likely cause", then the room line, the last event, the map and "Before this moment" at the side (`flow-ch-1440x900-dark-watch-prob2.png`). The last event is now printed once: on the line above the map, and absent from the "Before this moment" rows (moment 4 shows "3:32 Picked up Useless" above and 0:16 to 3:19 below). The caption fits at every size and moment I measured (see round-3 table). One small repeat is left: the summary partly restates the quote. At 1280 x 720 the clip is 548 x 308 in a column about 800 px wide, so it is not as big as it could be. |
| 4 | Can play the session and understand what happens between moments | 9 | Big clock, "Up next: moment 4 at 3:52, Code Lock, Ground floor", the next stop's quote, summary and cause in the left column, the map at two thirds with the trail, "Game events so far" (`sess-ch-1920x1080-dark-04.png`, `sess-ch-1280x720-dark-04.png`, `sess-we-960x1080-dark-04.png`). It stopped at moments 4, 7 and 8 in about 75 s, never at a by-design one, and the clip took over without a jump. On a phone the walk is readable, but the map sits below the caption, so the player's position needs a scroll (`sess-ch-400x860-light-04.png`). |
| 5 | Finds a dropped candidate and its reason without hunting | 9 | "4 dropped" in the header line and in the map legend scrolls to "Dropped moments" with the reason under each headline (`ch-her-spark-1440x900-dark-dropped-list.png`). In Watch the reason is the headline, the counter reads "Dropped 1 of 4", Previous and Next stay inside that list, and Escape returns to the row of the last one viewed. A dropped candidate still lists "Paused" and "Resumed" under "Before this moment", which adds nothing (low defect 5). |
| 6 | Never wonders which mode they are in | 9 | Read is a page. Watch is a full-screen dialog with Back at the left and the counter in the middle ("Moment 4 of 24", "Dropped 1 of 4", "Walking to the next unplanned moment"). Previous is disabled at moment 1, Next at the last (`ch-his-960-bug-watch.png`). Back is one line at 390 px. With reduced motion and with scripts off the page still reads (`ch-his-nojs-960.png`: the Play button is hidden, the native clip controls remain). |
| 7 | Holds at 960 and on a phone | 8 | Phone: fixed. At 400, 390 and 360 the clip, the status line, the quote, the summary, the cause and the friction row stack in order with no overlap (`ch-her-spark-390x700-dark-watch1.png`, `ch-her-spark-360x640-dark-watch1.png`), and the map and the events scroll below. At 960 the clip is 651 x 366 and everything is readable, but about 300 to 330 px under "Game state and the checker's note" is empty and the map is a narrow tall strip (`ch-her-spark-960x1080-dark-watch1.png`, `ch-her-open-960x1080-dark-watch1.png`, `ch-his-960-bug-watch.png`). That is the video's size, so it keeps this point at 8 and not 9. |
| | **Overall** | **8.9** | Mean of the seven (62 / 7). |

**PASS.** Every point is 8 or more and I found nothing blocking and no wrong-data defect. The weakest point is 7 (960), a polish issue.

## Round-3 defects, one by one

Measured with `getBoundingClientRect` in Chromium and WebKit (same script as round 3: `.clipbox` bottom against the caption's top, and caption `scrollHeight` against `clientHeight`). Script `/tmp/r29/s/sizes.py` for the first problem, `/tmp/r29/s/allmoments.py` for every moment of every page.

| # | Round-3 defect | Result | Evidence |
|---|---|---|---|
| 1 | Watch at 720 px or less: the clip covers the quote | **Fixed** | Overlap is 0 at 720, 600, 400 x 860, 390 x 700 and 360 x 640 (round 3: 195, 153, 104, 157, 150), light and dark, in both engines, on all three pages I measured (her Spark, her Open, his Spark; his Open in the all-moments walk). Every one of the 24 + 32 + 8 + 13 moments at 400 x 860 and 360 x 640 also has 0 overlap. At 400 x 860 the clip is 368 x 207 and ends at y 271, the caption starts at 283 and the quote at 315 (round 3: clip ended at 271, quote at 167). At 360 x 640 the caption ends at 547 and the viewport is 640. The walk at 400 shows the same stacking under the clock (`sess-ch-400x860-light-04.png`). |
| 2 | Laptop heights: caption cut by 22 to 48 px with no cue | **Fixed** | Caption scroll overflow is 0 at 1280 x 720, 1366 x 768, 1536 x 864, 1440 x 900 and 1920 x 1080 (round 3: 48, 51, 22, 22, 0), and 0 for every moment of the four pages at 1280 x 720, 1366 x 768 and 960 x 1080. At 1280 x 720 the caption is 212 px high and ends at y 600, above the timeline, so the friction row and the "Game state and the checker's note" line are visible (`ch-her-spark-1280x720-dark-watch1.png`). The price: the clip at 1280 x 720 is 548 x 308 (round 3: 647 wide), see idea 4. |
| 3 | At 960 about 290 px under the caption is empty, the map is narrow and tall | **Not changed** | Same layout: clip 651 x 366, left column ends near y 660, the map column is about 260 px wide and 650 px tall. Measured gap above the timeline: about 300 px (her), about 330 px (his, Open). See new defect 1. |
| 4 | The last event printed twice | **Fixed** | Above the map once; "Before this moment" lists the events before that one. In the walk, "Game events so far" omits the line printed above the map ("0:16 Demo steal laptop activated" above, two other 0:16 rows below). The summary still partly restates the quote (low, not counted as a defect). |
| 5 | "Back" wraps to two lines at 390 px | **Fixed** | One line at 390 and 360 px (`ch-her-spark-390x700-dark-watch1.png`). I did not measure the button height. |
| 6 | Timeline pins pile up at 400 px | **Not changed** | Pins overlap at 400 and 360, and at 960 where several moments sit close (her Open: 20 to 32 around 19:30 to 20:00). See new defect 2. |
| 7 | Dropped moments show "Paused" and "Resumed" rows | **Not changed** | `ch-her-spark-1440x900-dark-dropped-watch.png` (7:40 Paused, 7:41 Resumed). |
| 8 | The model line is easy to miss | **Not changed** | Still 12 px, mono, under the session name. See idea 2. |

## New defects, most severe first

None blocks. These are what I would fix next.

1. **960 x 1080, Watch: a third of the left column is empty and the map is a narrow strip.**
   - Size and state: 960 x 1080, Chromium and WebKit, light and dark, every moment on all four pages. Also 900 to 1100 px wide to a lesser degree.
   - What happens: the clip (651 px wide) and caption end near y 660 and the left column is empty down to the timeline at y 977, about 300 px on her pages and about 330 on his Open page. The map takes the right column, about 260 px wide and 650 px tall, so the level is small and the pins are tiny.
   - Capture: `/tmp/r29/shots/ch-her-spark-960x1080-dark-watch1.png`, `ch-her-open-960x1080-dark-watch1.png`, `ch-his-960-bug-watch.png`.
   - Why it matters: this is the size the video shows the Open page and the Spark page beside each other. The clip is the main thing and could be larger, or the map could be read at a glance. This is the only thing that holds point 7 at 8.
   - Proposed fix: below about 1100 px put "Before this moment" under the caption in the left column and give the map the full width of the right column (or the whole row under the clip), so the left column is filled and the map is bigger.

2. **Timeline pins overlap where moments are close.**
   - Size and state: 400, 390 and 360 px always (the active pin's number is hidden under neighbours: "5", "9", "10 11", "22 24"), and at 960 on the busy Open page around 20:00 (`ch-her-open-960x1080-dark-watch1.png`, `ch-her-spark-400x860-light-watch1.png`).
   - What happens: numbers draw over each other. The pin still works, the active ring still shows, but a number cannot be read and the target is small.
   - Why it matters: low, since the timeline is a secondary control, but it is visible in every phone capture and in the Open page's video frame.
   - Proposed fix: hide the numbers below about 500 px and keep shapes only, or stagger pins into more rows when two are closer than a pin's width.

3. **Phone: the map is below the caption, also while the session plays.**
   - Size and state: 360 to 720 px wide, Watch, both while playing the walk and at a moment.
   - What happens: during the walk the first screen shows the clock, "Up next" and the next stop's words, and the map (where the player is and was) needs a scroll past about 300 px of caption (`sess-ch-400x860-light-04.png`). The task said reading only is fine on a phone, so this is a note, not a defect against the bar.
   - Proposed fix: while walking, show the map first and put the "Up next" words under it; at a moment keep the clip first.

4. **Smaller things, all low.**
   - Cold-loading a `#d-<id>` link opens Watch with focus on the body (a `#m<rank>` link puts focus on Play). Tested in both engines.
   - A dropped candidate lists "Paused" and "Resumed" under "Before this moment".
   - Light mode: the list badges are brown and the same moment's pin on the map is bright yellow, so the two look like different colors (both are legible).
   - At 1920 x 1080 and 1440 x 900 the map's legend, and "4 dropped" there, sit just below the first screen; the header line has the same link.

## Ideas that would raise the score most (all my proposals)

1. **Fill the 960 column** (defect 1). It is the video's width. Point 7 from 8 to 9, and a better first frame of the demo; overall from 8.9 to about 9.0.
2. **Give the model a visible tag**, for example a small chip by the session name ("Spark" or "Open"), so the two pages differ at a glance in the video. The words and the look are Sasha's call.
3. **Keep the pins readable on a narrow timeline** (defect 2): numbers off below about 500 px.
4. **Use the free width at 1280 x 720.** The clip is 548 px wide in a column about 800 px wide, because its height is capped by the caption and the timeline. A thinner timeline strip (about 105 px today) or a caption that sits beside the clip below 1400 px would give the clip 60 to 100 px more.
5. **Phone walk: map first** (defect 3), so "where the player is and was" is visible during Play without a scroll.

## What I did not check

- Real audio, a real screen reader, real iOS Safari or Android, Firefox, a real phone. Phone sizes are viewports in Chromium and WebKit, with no touch emulation.
- Playing the session to the end: I played about 75 s on her Spark page (moments 4, 7, 8). Other pages I opened at their first problem and walked moment by moment with Next, not by Play. His Open page: first screen at 1920, 1366, 960 and 400, and the overlap walk, nothing else. The upper-floor-only moments in Read, and the time-spent switch beyond toggling it once on her Spark page (it works: `ch-her-heat-1440.png`).
- Light-mode Watch at 960 and 400 beyond the captures named above, 200 percent zoom, print, keyboard use beyond Tab on the first screen (focus ring is a 2 px solid outline on the first problem link), arrows, Space and Escape in Watch, which behave: Right moves to the next moment, Left back, Space toggles play and pause.
- Contrast numbers (I judged by eye), the heat view at other sizes, and the button heights at 390.
- Wording, names and the look: Sasha's call. I did not compare to the mocks, read the code beyond what the measurements needed, or check numbers against `findings.json` (that is Grok's review). The recorded flow and captures named in task 37, and the unit tests.
