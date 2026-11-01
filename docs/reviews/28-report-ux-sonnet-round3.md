Reviewer: Claude Sonnet 5.5, Claude Code via T3. Round 3 of the UX loop. Commit a84618f. UX review with a score.

I used the four pages in `runs/final/` as a first-time level designer would: Chromium and WebKit through Playwright, from file://, at 1920 x 1080, 1440 x 900, 960 x 1080, 400 x 860 and 390 x 700, light and dark (plus a sweep of 17 other viewport sizes for the Watch layout). I did the seven points as tasks, played her Spark session for about 70 s at 10x (1920 in Chromium, 960 in WebKit, and the first 5 s of the walk at 400 and 390), and rechecked every round-2 defect. No console or page errors and no horizontal overflow on any of the four pages in either engine. I scored from the pages, not from earlier numbers. Captures are in `/tmp/r28/shots/`, scripts in `/tmp/r28/s/`. Nothing was copied into the repo.

## Score

| # | Point | Score | Why |
|---|---|---|---|
| 1 | Knows what went wrong and where in a few seconds | 9 | Session name, the model line, the count headline, "4 dropped" and "5:42 stuck or blocked", Play, five ranked problems with kind shapes and the map with pins all fit the first 1080 px at 1920, 1440 and 960 (`ch-her-spark-1920x1080-dark-first.png`, `ch-her-spark-960x1080-dark-first.png`). His demo's top problem is a pink triangle on the map edge with a dashed ring, and the name "Laboratory" is the first link (`ch-his-spark-1920x1080-dark-first.png`). The headline counts moments but does not name the worst place; the list under it does, at once. |
| 2 | Problem to clip in one click, back in one | 9 | A title, a badge, a map pin and a dropped row each open Watch in one click. Back and Escape return with the opener focused and the scroll position kept, now also from a scrolled start: from scrollY 150 and 400 both Escape and Back landed on the same scrollY with focus on the title or the badge, in both engines. After Next from moment 12 to 13, Back scrolled to moment 13's row (focus on its clip button), which is the right "where I came from". |
| 3 | At a moment: big clip, words, cause, where, nothing repeated | 8 | At 1920, 1440 and 960 the order is right: clip, status line, the quote as headline, the summary, "Likely cause", then the map and "Before this moment" at the side (`ch-her-spark-1920x1080-dark-watch-p1.png`). The room line now matches the caption on his page ("Laboratory, Ground floor" in both). Still repeated: the last game event is printed above the map and again as the bold last row of "Before this moment", and the summary restates the quote. At 1280 x 720 and 1366 x 768 the friction row and "Game state and the checker's note" are cut off inside the caption box (new defect 2). On a phone the quote is hidden, see new defect 1. |
| 4 | Can play the session and understand what happens between moments | 9 | Same strength as round 2: the big clock, "Up next: moment 4 at 3:52, Code Lock, Ground floor", the next stop's quote, summary and cause in the left column, the map at two thirds with the trail, "Game events so far" (`sess-1920-ch-04.png`, `sess-960-we-04.png`). It stopped at moment 4, then 7, then 8 in about 70 s, never at a by-design one. At 400 the same walk is readable but the same overlap as defect 1 sits under the clock (`ch-her-390x700-dark-walk.png`). |
| 5 | Finds a dropped candidate and its reason without hunting | 9 | "4 dropped" in the header line and in the legend scrolls to "Dropped moments" with the reason under each headline (`ch-dropped.png`). In Watch the reason is the headline, the counter reads "Dropped 2 of 4" and Previous and Next stay in that list (`ch-her-watch-dropped.png`). |
| 6 | Never wonders which mode they are in | 9 | Read is a page, Watch is a full-screen dialog with Back on the left and the counter in the middle ("Moment 4 of 24", "Dropped 2 of 4", "Walking to the next unplanned moment"). Previous is now disabled at moment 1 and Next at moment 24 (checked: `prev` true at 1 of 24, `next` true at 24 of 24; the arrow keys also do nothing there). At 390 px "Back" wraps to two lines, small. |
| 7 | Holds at 960 and on a phone | 6 | 960 is better than round 2: the clip is 651 x 366 px (it was about 576 x 320) and the quote, cause and map are all visible (`ch-her-spark-960x1080-dark-watch-p1.png`), but about 290 px under the caption is still empty and the map column stays narrow and tall. 400 px Read is clean (`ch-her-spark-400x860-light-first.png`). 400 px and 390 px Watch is broken: the clip is drawn over the top 100 to 160 px of the caption, so the headline quote, the status line and part of the summary are hidden (new defect 1). The round-2 fix removed the nested scroller and introduced this overlap. |
| | **Overall** | **8.4** | Mean of the seven (59 / 7). |

**NOT PASS.** Point 7 is 6, below the bar of 8, because of one blocking defect: on any viewport 720 px wide or less, Watch hides the quote, the thing point 3 and the "words" line of the layout depend on. Everything else is 8 or 9 and I found no wrong-data defect.

## Round-2 defects, one by one

| # | Round-2 defect | Result | Evidence |
|---|---|---|---|
| 1 | Watch at a phone width: caption in a tiny nested scroller | **Not fixed, replaced by a worse one** | The inner scroller is gone (`.caption { overflow: visible }`), but `.screen` now gives its first row only about 70 px, so the 16:9 clip (207 px high at 400, 201 px at 390) paints over the caption. Measured with `getBoundingClientRect` in Chromium, and the 400 x 860 numbers repeat in WebKit: at 400 x 860 the clip ends at y 271 while the caption starts at 135 and its quote at 167 (104 px of the quote hidden); at 390 x 700 the clip ends at 265 and the quote starts at 108 (157 px overlap); at 700, 600 and 500 px wide the overlap is 195, 153 and 117 px. At 721 px and above it is 0. Captures: `ch-her-400x860-main-top.png`, `ch-her-spark-400x860-light-watch-p1.png`, `ch-her-spark-390x700-dark-watch-p1.png`. |
| 2 | Previous at the first moment and Next at the last look active | Fixed | `disabled` true on Previous at "Moment 1 of 24" and on Next at "Moment 24 of 24", with a dimmed look (`ch-her-spark-1920x1080-dark-watch-p1.png` shows it on his page at 8 of 8: "Next" is dim). While walking, Previous stays active and Next goes dim only when there is nothing ahead. |
| 3 | The line above the map and the caption can name different places | Fixed | His moment 8: the line and the caption both say "Laboratory, Ground floor", and the off-map note and the last event "8:03 Archive door opened (Archive)" remain as honest context. Her moment 4: both say "Code Lock, Ground floor". While walking the line still says "Between rooms" or the player's room, which is correct there. |
| 4 | At 960 the clip is not big | Partly fixed | Clip 651 x 366 at 960 (was about 576 x 320); the main grid now splits 5 to 2 below 1100 px. The empty area under the caption and the narrow map column remain (new defect 3). |
| 5 | Light mode: dark digits on a mid-brown fill in the badges | Fixed | White digits on the brown fill (`ch-noscript-1440-light.png`, `ch-her-spark-1440x900-light-watch-p1.png`). I estimate about 5.2:1. The badge in the list is brown and the same moment is a bright yellow pin on the map, so the two still look like different colors in light mode, but both are legible. |
| 6 | The model line is easy to miss | Not changed | Still 12 px, dim, under the session name (`ch-her-open-960x1080-dark-first.png`). The headline counts differ between the pages, so the pages are distinguishable; the model is not. See idea 4. |

## New defects, most severe first

1. **Watch at 720 px wide or less: the clip covers the quote and the head of the caption.**
   - Size and state: every viewport up to 720 px wide, tested at 720, 600, 500, 400 x 860, 390 x 700 and 360 x 640; Chromium and WebKit, light and dark. Opening any moment (a problem title, a badge, a pin, a moment still) or "Play the session" gets there. Overlap in px of the clip over the text: 195 (720), 153 (600), 117 (500), 104 (400 x 860), 157 (390 x 700), 150 (360 x 640).
   - What happens: the grid row above the caption is about 70 px high, the clip is 200 to 390 px high, so the clip is painted over the caption. The status line, the headline quote and often the first line of the summary are hidden. At 390 x 700 only "how to open after failed tries" of the cause is visible. The "4" badge of the status line shows through at the clip's left edge (it is the part of the caption's first row that sticks out), which reads as a stray mark. The same overlap sits below the clock while the session walks.
   - Capture: `/tmp/r28/shots/ch-her-spark-390x700-dark-watch-p1.png`, `ch-her-spark-400x860-light-watch-p1.png`, `ch-her-400x860-main-top.png` (main scrolled to the top, same result), `ch-her-390x700-dark-walk.png`. Measurement script `/tmp/r28/s/sizes.py`.
   - Why it matters: this is point 7 and the heart of point 3. The words and the likely cause are what a designer came for, and a tap on any problem on a phone lands here. It is also a regression in the sense that round 2 saw the text clipped in a scroller and the fix made it unreachable.
   - Proposed fix: I did not isolate the cause beyond the numbers. Below 720 px make `.screen` a plain block (`display: block`, or `grid-template-rows: none`) so the clip box and the caption stack by normal flow, and check the `aspect-ratio` clip box inside an `auto` grid row. Verify with the same overlap measurement at 360, 400, 500, 600, 720 px.

2. **Laptop-height screens: the caption is cut by 22 to 48 px with no cue.**
   - Size and state: 1280 x 720 (caption box 156 px, content 204 px), 1366 x 768 (156 / 207), 1536 x 864 (156 / 178), 1440 x 900 (187 / 209). Chromium. At 1920 x 1080 it fits (187 / 187).
   - What happens: the friction row ("High, Abandoned") and "Game state and the checker's note" are below the fold of the caption box. The caption scrolls inside itself, but nothing shows that there is more (`ch-her-1280x720-dark-watch-p1.png`: the clip is 647 px wide in an area about 830 px wide, so there is room).
   - Why it matters: these are very common laptop sizes, and the "Abandoned" tag and the checker's note are part of point 3 ("where and what happened") and point 5 (reasons).
   - Proposed fix: shrink the reserve in the clip's width formula (the `200px` in `.clipbox`) a little so the caption gets the 50 px, or let the caption row grow and scroll the left column as a whole.

3. **At 960 x 1080 about 290 px under the caption is empty and the map is a narrow tall strip.**
   - Size and state: 960 x 1080, Chromium, light and dark. Also 900 and 1100 px wide, to a lesser degree.
   - What happens: the clip is bigger than before (651 x 366), but the left column ends at the "Game state" line and leaves a large empty area, while the map is about 260 px wide and more than 650 px tall (`ch-her-spark-960x1080-dark-watch-p1.png`, `ch-her-open-960x1080-dark-watch-p1.png`). This is the size the video shows.
   - Why it matters: the clip is the main thing and could take 60 to 100 px more height, or "Before this moment" could move under the caption.
   - Proposed fix: below about 1100 px put "Before this moment" under the caption in the left column, or give the clip the whole row at 960 and put the map beside the caption.

4. **Smaller things, all low.**
   - The last game event is printed twice (the line above the map and the bold last row of "Before this moment"). The summary often restates the quote. Point 3 says "nothing repeated".
   - At 390 px the "Back" button wraps to two lines and the three buttons are 37 px high.
   - Timeline pins pile up at 400 px (`ch-her-spark-400x860-light-watch-p1.png`); the problem badges on Read are about 24 px.
   - The model line is easy to miss (round 2, defect 6, unchanged).
   - Dropped moments show "Before this moment" rows such as "Paused" and "Resumed", which add nothing for a dropped candidate (`ch-her-watch-dropped.png`).

## Ideas that would raise the score most (all my proposals)

1. **Fix the phone overlap** (defect 1). It is the one thing under 8. Point 7 from 6 to 8 or 9, point 3 and 4 safer; overall from 8.4 to about 8.9.
2. **Make the caption fit at 1280 x 720 to 1536 x 864** (defect 2). Point 3 from 8 to 9 on the most common laptop sizes.
3. **Use the 960 empty space** (defect 3). It is the video's width. Point 7 from 8 to 9 and a better first look in the demo.
4. **Give the model a visible tag**, for example a small chip by the session name ("Spark" or "Open") so the two pages differ at a glance in the video. The words and the look are Sasha's call.
5. **Print the last game event once.** Drop it from the line above the map (keep the bold last row of "Before this moment") or the other way round. Point 3 to 9 or 10.

## What I did not check

- Real audio, a real screen reader, real iOS Safari or Android, Firefox, and a real phone. Phone sizes are viewports in Chromium and WebKit, with touch emulation in the walk checks only.
- Playing the session to the end: I played about 70 s at 1920 (Chromium) and 960 (WebKit), and the first 5 s at 400 and 390. The Open pages only in Watch at their first problem (1920, 960, 400), and his pages at 1440, 400 dark and light Watch. The upper-floor-only moments in Read.
- Light-mode Watch at 960 and 400 (captured, not looked at beyond the 1440 and 400 views), Back from a deep link (`#m9`, `#d-...`), and the Open pages' Back from a scrolled start (I tested her Spark page only; the code is shared).
- Reduced motion beyond "Play the session starts a walk and Escape returns"; print; keyboard-only use beyond Tab on the first screen, arrows (five Right presses gave moment 9), Space, Enter and Escape; 200 percent zoom.
- Wording, names and the look: those are Sasha's call. I did not compare to the mocks, read the code beyond the overlap's CSS, or check numbers against `findings.json` (that is Grok's review). The recorded flow and the captures named in task 37 and the unit tests.
