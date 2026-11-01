Reviewer: Claude Sonnet 5.5, Claude Code via T3. Round 2. Commit 952ecb1 (task 38, Claude Fable 5.1). UX review with a score.

I used the four pages in `runs/final/` as a first-time level designer would: Chromium and WebKit through Playwright, from file://, at 1920 x 1080, 1440 x 900, 960 x 1080, 400 x 860 and 390 x 700, light and dark. I did the seven points as tasks, played her Spark session for 65 s at 10x at 1920 (Chromium) and 960 (WebKit), and rechecked every round-1 defect. No console or page errors on any of the four pages in either engine, and no horizontal overflow at 400 px. I scored from the pages, not from round 1's numbers. Captures are in `/tmp/r26/shots/`, scripts in `/tmp/r26/s/`. Nothing was copied into the repo.

## Score

| # | Point | Score | Why |
|---|---|---|---|
| 1 | Knows what went wrong and where in a few seconds | 9 | The verdict, the "Analyzed with" line, five ranked problems with kind shapes and the map with pins all fit the first 1080 px at 1920, 1440 and 960. The route now recedes, so pins 14, 15, 19 and the hollow dropped pins read (`her-spark-1920-dark-first.png`, `zoom-ovmap-light-2x.png`). His demo's top problem now sits at the map edge with a dashed ring instead of being cut off (`his-spark-1920-dark-first.png`). |
| 2 | Problem to clip in one click, back in one | 9 | A problem title, a badge or a map pin opens Watch in one click, and Escape or Back returns to the same spot with the opener focused (title, badge and pin each checked, Chromium and WebKit, light and dark). I clicked every pin on both floors of all four pages by real mouse position and each opened its own moment. |
| 3 | At a moment: big clip, words, cause, where, nothing repeated | 8 | The layout is right: clip about two thirds, the quote as headline, summary and "Likely cause" under it, the map and "Before this moment" at the side (`ch-dark-watch-p1.png`). Small repeats and mismatches remain: the last game event is printed above the map and again as the last "Before this moment" row, the summary restates the quote, and the line above the map can name another place than the caption ("Between rooms" while the player faces the Archive door). The words fall apart on a phone, see new defect 1. |
| 4 | Can play the session and understand what happens between moments | 9 | While walking, the clip shows a big clock, the native controls are gone, the left column shows "Up next" with the next stop's head, quote, summary and cause, the map takes two thirds and follows the floor, and the events so far scroll (`sess-1920-ch-04.png`, `sess-960-we-04.png`). It stopped only at unplanned moments (4, then 7, then 8 in 65 s). Space and Escape work during the walk. |
| 5 | Finds a dropped candidate and its reason without hunting | 9 | "4 dropped" is a link in the header line and in the map legend. It scrolls to "Dropped moments" (no Watch). Every dropped row shows its reason (`her-1920-dark-read-dropped.png`). In Watch the reason is the headline, the counter says "Dropped 1 of 4", and Next stays in that list. |
| 6 | Never wonders which mode they are in | 9 | Read is a page, Watch is a full-screen dialog with Back on the left and "Moment 4 of 24", "Dropped 1 of 4" or "Walking to the next unplanned moment" in the middle. The Play/Pause button reads (7.88:1 dark, 7.51:1 light, both engines, both states). Space plays or pauses and never closes Watch. Previous at the first moment and Next at the last do nothing and look active (new defect 2). |
| 7 | Holds at 960 and on a phone | 7 | 960: no overflow, the first screen stays complete and the model name tells the Open page from the Spark page (`her-open-960-dark-first.png`, `her-spark-960-dark-first.png`). Watch at 960 works but the clip is only about 580 px wide with a large empty area under the text (`we-960-dark-watch-m4.png`). 400 px Read is clean (`we-400-light-read-map.png`). 400 px Watch breaks: the quote, summary and cause sit in a 114 px (400 x 860) or 40 px (390 x 700) nested scroller (new defect 1). |
| | **Overall** | **8.6** | Mean of the seven (60 / 7). |

**NOT PASS.** One point is below 8 (point 7) because of one defect (new defect 1). It is a small CSS fix. Nothing else blocks, and I found no wrong-data defect.

## Round-1 defects, one by one

| # | Round-1 defect | Result | Evidence |
|---|---|---|---|
| 1 | Play/Pause unreadable (blocking) | Fixed | Computed text on background: 7.88:1 dark (`rgb(11,16,32)` on `rgb(141,162,255)`), 7.51:1 light (white on `rgb(47,69,199)`), identical for "Play" and "Pause", Chromium and WebKit. `ch-dark-watch-p1.png`, `ch-light-watch-p1-b.png`. |
| 2 | Space closes Watch right after it opens | Fixed | After clicking a top problem, focus is on Play. Space gives paused true, Space again plays; Watch stayed open (Chromium and WebKit, light and dark). Space during the walk toggles Play/Pause. |
| 3 | Back lands in the wrong place | Fixed | From the first problem title: Escape gives scrollY 0 and focus on that title. From badge 14 in problem 3: Back gives scrollY 0 and focus on "Moment 14". From a map pin: Escape gives scrollY 0 and focus on the pin. From a dropped row: Escape returns to scrollY 6101 and focuses that row. After "Play the session", Escape returns to scrollY 0 with focus on the button, and the walk stops (clock frozen at 0:46 for 35 s). I only tested openers from scrollY 0, so "restores the scroll position" is shown for the first screen, not for a scrolled start. |
| 4 | His demo: #1 problem half off the map, header contradicts the caption | Mostly fixed | The pin is clamped inside the map and drawn with a dashed ring (`his-spark-1920-dark-first.png`). In Watch a line says "This moment is outside the mapped area. Its pin sits at the map's edge." (`his-spark-1920-dark-watch-p1.png`). The line above the map still says "Archive, Ground floor" while the caption says "Laboratory, Ground floor". The note explains it, but the two places are still not reconciled (new defect 3). |
| 5 | The faint route is too heavy | Fixed | The route is a thin pale line with no dark casing. Pins 14, 15, 19, 11 and the hollow dropped pins are clear at 2x (`zoom-ovmap-light-2x.png`). The 30 s trail stays loud (`ch-dark-watch-p1.png`). |
| 6 | Open page looks the same as the Spark page | Fixed, small | "Analyzed with meta-models/muse-spark-open-1026." sits under the session name, in 12 px dim mono. Next to the Spark page at 960 it is the only text difference besides the counts (`her-open-960-dark-first.png`). It works but is easy to miss (idea 5). |
| 7 | Dropped candidates not linked from the first screen | Fixed | Clicking "4 dropped" from the top: URL `#dropped`, scrollY 6114, Watch stays closed, the heading is in view (`her-1920-dark-read-dropped.png`). |
| 8 | Walking: empty left half, overlay on native controls | Fixed | `controls` is false while walking and true at a clip. "Up next" fills the left column (`sess-1920-ch-04.png`, `sess-960-we-04.png`). At 960 the clock and the "Up next" text no longer touch the progress bar. |
| 9 | Stale frame when a walk restarts | Not reproduced | Two walks in the 65 s run, in both engines: 0:41 at the first poll for the first walk, 4:26 (1920) and 4:23 (960) for the second, "Up next" correct each time. |
| 10 | Next from a dropped candidate jumps lists | Fixed | "Dropped 1 of 4" then Next gives "Dropped 2 of 4". Previous and Next stay in the list the counter names. |
| 11 | 400 px Watch: timeline labels collide, small tap targets | Partly fixed | Axis labels are every 4:00 and no longer collide. Pins pile up in the timeline at 400 (`ch-400-light-watch-m4.png`). Problem badges are still 24 x 24 px; the Back, Previous, Play and Next buttons are 37 px high. Low, reading only is accepted. |

The orchestrator's second question in round 1 (the faint route against the 30 s trail) is answered by defect 5: the trail wins in Watch and the route no longer dominates Read.

## New defects, most severe first

1. **Watch at a phone width: quote, summary and cause sit in a tiny nested scroller.**
   - Size and state: 400 x 860 (caption 114 px tall holding 287 px of text) and 390 x 700 (caption 40 px tall holding 312 px), Chromium and WebKit, light and dark. Measured with `getBoundingClientRect` and `scrollHeight` on `#caption`. Anything that opens Watch gets there: a problem title, Play the session, a moment still.
   - What happens: the quote is cut mid-line ("... that can help" ends at a clipped edge), and the summary and "Likely cause" are not visible at all. The only way to see them is to scroll inside the small caption box, which sits inside the scrolling main column. Wheeling over the clip scrolls the outer column instead, so the reader may never find them.
   - Capture: `/tmp/r26/shots/ch-390x700-dark-watch-m4.png`, `/tmp/r26/shots/ch-400-light-watch-m4.png`.
   - Why it matters: point 3 needs the quote and the cause, and point 7 needs the same on a phone. Read at 400 px shows all of this fine, so the data is there, but Watch hides it.
   - Proposed fix: below about 700 px let `#caption` grow to its content (no height cap, no inner scroll) and let `.main` carry the one scroll. At 700 px or less in height, the 52 px top bar plus the 104 px timeline already take a fifth of the screen.

2. **Previous at the first moment and Next at the last do nothing and look active.**
   - Size and state: all sizes. At "Moment 1 of 24" Previous, and at "Moment 24 of 24" Next, are enabled (`disabled` false) and a click or the arrow key changes nothing.
   - Why it matters: it reads as a stuck button, in the one mode where a designer pages quickly.
   - Proposed fix: disable the button at either end, or say "First moment" or "Last moment" in the counter.

3. **The line above the map and the caption can name different places.**
   - Size and state: his Spark page, moment 8, 1920 and 960. The line says "Archive, Ground floor, 8:03 Archive door opened (Archive)"; the caption says "Laboratory, Ground floor". The dashed note explains the off-map pin but not the room name. On her page, at moment 4 about 8 s into the clip, the line reads "Between rooms, Ground floor" while the player faces the Archive door and the caption says "Code Lock" (`we-960-dark-watch-m4.png` and `sess-960-we-12.png`).
   - Why it matters: it is the same "two places for one moment" confusion round 1 raised. It is small now, but it sits next to the headline of the demo's top problem.
   - Proposed fix: print "Clip starts in Archive" when the clip's room differs from the moment's room (the words are Sasha's call), or take the room from the moment's own room when the route point falls between polygons.

4. **At half a screen (960 x 1080) the clip is not "big".**
   - Size and state: Watch at 960, both engines. The clip is about 576 x 320 px; the map column is tall and narrow; about 330 px under the caption in the left column is empty (`we-960-dark-watch-m4.png`).
   - Why it matters: this is the size the video uses ("the Open page beside the Spark page"). The clip is the main thing and gets a third of the area.
   - Proposed fix: below about 1100 px wide give the clip about 66 percent, or move "Before this moment" under the caption into the empty space and let the map be shorter.

5. **Light mode: dark digits on a mid-brown fill in the Top problems badges and the timeline.**
   - Size and state: all sizes, light. Text is `rgb(27,19,0)` on a `rgb(148,98,0)` fill, about 3.5:1 by my calculation, at 10.8 px bold. The same moment is a bright yellow pin on the map, so the badge in the list and the pin look like different colors (`her-spark-1920-light-first.png`, `zoom-tl-light-2x.png`).
   - Why it matters: legible but weak, and the badge-to-pin link is the first-screen glance the layout depends on. Dark mode is fine (10:1).
   - Proposed fix: use the pin's fill for the badge in light mode, or white digits on the brown.

6. **The model line is easy to miss.**
   - Size and state: all sizes. 12 px, dim, directly under the session name.
   - Why it matters: it works for a reader who looks, and the video plan relies on a judge telling the two pages apart. Low.
   - Proposed fix: see idea 5.

## Ideas that would raise the score most (all my proposals)

1. **Fix the phone Watch caption** (defect 1). It is the one thing keeping point 7 under 8, and the fix is a few CSS lines. Point 7 from 7 to 8 or 9.
2. **Make the two places agree** (defect 3): one short line when the clip starts in a room other than the moment's room. It turns the demo's best moment, the Laboratory bug, into a clean read. Points 3 and 6 up by one.
3. **Disable Previous and Next at the ends** (defect 2). Five lines and the paging feels finished. Point 6 to 9 or 10.
4. **Use the 960 empty space** (defect 4): a bigger clip, or "Before this moment" under the caption. It matters most because the video shows this width. Points 3 and 7 up by one.
5. **Give the model a visible tag**, for example a small chip by the session name ("Spark" or "Open"), so side-by-side pages differ at a glance. The words and the look are Sasha's call. Point 1 and the video story.

## What I did not check

- Real audio, a real screen reader, real iOS Safari or Android, Firefox, and a real phone. Phone sizes are viewports in Chromium and WebKit, one with touch emulation.
- Playing the session to the end (I played about 65 s at 1920 and 65 s at 960), the upper-floor-only moments in Read, and the Open pages in Watch beyond the first problem (his Open at 960 and 1920, her Open at 1920 and 960, one moment each) and the first screens. The Open pages at 1440 and 400, and his pages at 1440, 400 and light.
- Back from a Top problem opener when the page was already scrolled down; I tested openers from scrollY 0 only. Back from a deep link (`#m9`, `#d-...`) beyond the fact that Watch opens; WebKit left the page at scrollY 0 and focus on the body for the dropped deep link, Chromium scrolled to the row. I did not follow it further.
- Reduced motion beyond "Watch opens"; print; keyboard-only use beyond arrows, Space, Escape, Enter and a short Tab pass; 200 percent zoom.
- Wording, names and the look: those are Sasha's call. I did not compare to the mocks, check the code, or check numbers against `findings.json` (that is Grok's review).
- The recorded flow `/tmp/t38/flow.webm` and the claim of captures in `/tmp/t38/shots/`; the unit tests.
