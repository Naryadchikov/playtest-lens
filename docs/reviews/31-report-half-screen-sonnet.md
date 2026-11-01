Reviewer: Claude Sonnet 5.5, Claude Code via T3. Commit 5d7400a. Half-screen layout check.

I opened her Spark page, her Open page and his Spark page from `runs/final/` in Chromium and WebKit through Playwright (file://). Sizes: 960 x 1080, 1100 x 900, 900 x 1000, 721 x 900, plus 960 x 1040, 1000, 950 and 900, 1000 x 900, 1000 x 800, 1024 x 768, 1100 x 800, 1100 x 1000 and 800 x 800 to find where the layout breaks. Spot checks at 1440 x 900, 1920 x 1080 and 400 x 860. Light and dark. For comparison I made an "old" copy of each page in `/tmp/r31/old/` by cutting the new media block out of the HTML, so every claim below about "before" is measured on the same data, not remembered.

What I did: at every size I walked every moment of all four pages (her Spark 24, her Open 32, his Spark 8, his Open 13) with the arrow keys and measured the clip, caption, place line, map and "Before this moment" boxes against the timeline and each other; opened a dropped candidate and his off-map moment 8 at all four sizes in both engines; stepped with Previous and Next by click; played her Spark session for about 78 s at 960 x 1080 (Chromium dark, WebKit light) and logged every animation frame across four walking/moment switches. Captures are in `/tmp/r31/shots/`, scripts in `/tmp/r31/s/`. Nothing was copied into the repo. No console or page errors and no horizontal overflow anywhere.

## Verdict

**NOT PASS.** The target size is better and walking, 1440, 1920 and 400 px are unchanged, but the new layout is a regression on short windows between 721 and 1100 px wide: the upper-floor map and the "Before this moment" list run under the timeline and are cut, with no scroll. The old layout fit at those sizes. It is a small CSS fix (defect 1).

## Point 7 (half a screen and a phone): 8, unchanged

| Size | What I saw |
|---|---|
| 960 x 1080 (the video) | Clean. Clip 651 x 366 in the left column, the quote, summary, cause, friction row, "Game state" line and "Before this moment" (4 events) under it, the place line and the map at the right. No overlap, nothing cut, in both engines, light and dark, every moment on all four pages. Also fine at 960 x 1040, 1000, 950 and 900 (`ch-her-spark-960x1080-dark-m1.png`, `we-his-spark-960x1080-dark-m1.png`, `drop-her-spark-960x1080-light.png`). |
| 900 x 1000, 721 x 900 | Clean, same arrangement; the clip is 609 and 481 px wide, the map 243 and 192 px (`ch-her-spark-721x900-dark-m1.png`, `off-his-spark-721x900-dark.png`). |
| 1100 x 900 | Fine on the ground floor; the upper floor of her Open page is cut (defect 1). |
| 1000 x 800, 1024 x 768, 1100 x 800 | Cut on every moment, events and upper-floor map (defect 1). |
| 400 x 860 | Same boxes as before, to the pixel (clip ends 271, quote starts 315, no overflow). |

Why it stays at 8 and not 9:
- The empty space at 960 x 1080 is smaller, not gone. Before: about 300 px empty under the caption, with the map filling the right column. Now: "Before this moment" fills about 100 px of the left column, so the left gap is about 230 px (events end near y 745, the timeline starts at 977). The map panel now shrinks to the map, so the right column has its own gap: about 230 px under an upper-floor map, about 420 px under a ground-floor map (`ch-her-spark-960x1080-dark-m1.png`). Both columns end in blank space above the timeline.
- The map did not get bigger. It is 261 px wide at 960 before and after (measured on the same moment in the old and new copies: `cmp-old-960x1080.png` against `cmp-new-960x1080.png`). Round 4's "narrow strip" complaint is about the map's width, and that is unchanged. Her upper floor still draws pins 7 to 13 as a cluster you cannot read at that size (`walk-ch-960x1080-dark-04.png`). Only the empty panel around the map got shorter.
- The regression in defect 1.

What is good: the clip is still the main thing (651 of 928 px wide), the quote is directly under it, the events moved from squeezed-under-the-map to under the caption where the eye already is, and both columns line up at the top. At 721 the right column is 192 px but the room line wraps cleanly and the map keeps its aspect ratio.

## Points 3 and 4

- **Point 3 (at a moment: big clip, words, cause, where, nothing repeated): 9, unchanged at the bar sizes** (960 x 1080, 1440, 1920, 400). The order is the same and nothing is repeated. At 1000 to 1100 px wide and 800 to 850 px high it is worse than before: the newest events, the ones nearest the moment, are the ones cut off (defect 1).
- **Point 4 (play the session and understand what happens between moments): 9, unchanged.** The walking layout is identical to the old one at 960, 1100 and 721 (same five boxes, same pixels). The session played at 960 x 1080 in both engines and stopped at moments 4, 7 and 8 without an error. The clip takes over at a moment as an animation (0.35 s, widths glide), with one small visual hop (defect 3).

## Checks on the other sizes

- 1440 x 900, 1920 x 1080, 1280 x 720, 1101 x 900, 720 x 900, 600 x 900, 400 x 860: the clip, caption, place line, map, events and timeline boxes are identical in the old and the new copy, in both engines, for three moments each. At 721 x 900 the caption box is shorter (238 instead of 438) because it no longer stretches, which is the intended change.
- 400 px spot check: clip ends at y 271, the quote starts at 315, the page does not scroll sideways, in both engines, light and dark. No regression.
- 1440 x 900 and 1920 x 1080: clip bottom 556 / quote top 600 and 736 / 780, the same numbers as round 4.
- Dropped candidate, "Dropped 1 of 4": Previous disabled, reason as the headline, events under the caption, no overlap (`drop-her-spark-960x1080-light.png`).
- His moment 8, off the map: the note "This moment is outside the mapped area..." sits above the floor switch, the map starts at y 195 (960) or 239 (721), nothing overlaps (`off-his-spark-721x900-dark.png`, `we-his-spark-960x1080-dark-m1.png`). The pink triangle sits on the map edge as before.
- The room line is cut with an ellipsis at 721 (the "last event" line). It was the same in the old layout and is by design (`white-space: nowrap`).

## Defects, most severe first

1. **Short windows, 721 to 1100 px wide: the map and the events run under the timeline and are cut. A regression from 5d7400a.**
   - Size and state: any Watch at a moment when the viewport is about 1000 to 1100 px wide and 800 px high or less (1000 x 800, 1024 x 768, 1100 x 800), and on the upper floor also at 1100 x 900. Chromium and WebKit give the same numbers, light and dark. Also 800 x 800 (events only).
   - Measured, new layout, distance below the timeline's top edge, worst moment: the upper-floor map 98 px at 1000 x 800, 145 at 1024 x 768, 162 at 1100 x 800, 62 at 1100 x 900 (all on her Open page, moment 18 and the other upper-floor moments; 9 of her Open's 32, 6 of her Spark's 24, 3 of his Spark's 8). The last "Before this moment" row sits 86 px under the timeline at 1000 x 800 on 22 of 24 moments of her Spark page and 31 of 32 on her Open, and 9 px at 1100 x 900. On the old copy the same sizes measured: map at least 81 px above the timeline, events fully above, nothing under it, on every moment.
   - Capture: `/tmp/r31/shots/cut-1000x800-worst.png` (the fourth event is half hidden, the map ends mid-floor at the screen edge), `/tmp/r31/shots/cut-1100x900-worst.png`.
   - Why it matters: it is the same class as round 3's cut caption: content hidden with no scrollbar and no cue. The events cut are the newest ones, the ones that explain the moment. The upper-floor map is the one with pins in it, and the part past the timeline is not there to see. It affects anyone who opens the report on a 1024 x 768 tablet or a 1100 x 800 laptop window. It does not affect the video size (960 x 1080 and a browser window of about 960 x 950 are both fine).
   - Cause (from the diff): `.maps .floor svg { width: 100%; height: auto; max-height: none }` makes the map grow with the column width regardless of the window height, and `.before` has no bottom limit in this layout.
   - Proposed fix (Sonnet's, the orchestrator decides): in the same media block give the map a height cap instead of `max-height: none`, for example `max-height: calc(100vh - var(--bar-h) - var(--tl-h) - 190px)` with `width: auto; max-width: 100%` so it keeps its aspect ratio, and give `.before` `min-height: 0; overflow: auto` so a short window scrolls the events instead of cutting them. Re-run the all-moments walk at 1000 x 800 and 1100 x 900 to confirm 0 under the timeline. A smaller alternative is to leave the new layout on only when `(min-height: 880px)` and keep the old one below that.

2. **At 960 the map is still small (261 px) and the right column now has its own empty space.**
   - Size and state: 960 x 1080, 900 x 1000, every moment (`ch-her-spark-960x1080-dark-m1.png`, `walk-ch-960x1080-dark-04.png`).
   - What happens: the map is the same size as in round 4, its panel is just shorter. About 230 px (upper floor) to 420 px (ground floor) is blank under it. On the upper floor the cluster 7 to 13 is a few pixels apart.
   - Why it matters: this is what keeps point 7 at 8. The game space is the point of the page, and half a screen has room for it.
   - Proposed fix: at 721 to 1100 px give the map more of the row, for example columns `3fr 2fr` (the clip drops from 651 to about 540 px, still the main thing) so the map is about 370 px wide, or let the map cell run the full height down to the timeline. This is a proposal for a look change, which is Sasha's call.

3. **At the switch between walking and a moment, "Before this moment" jumps in one frame, and the map is briefly taller than the window.**
   - Size and state: 960 x 1080, Chromium, from the frame log of the walk (`/tmp/r31/s/jump.py`). In the first frame after the switch the events block moves from under the map on the right (x 336, y 866) to under the caption at the left (x 16, y 540), while the clip, caption and map animate smoothly over 0.35 s. In that first frame the map is 836 px tall (it ends at y 989, the timeline starts at 977) and it shrinks to 400 to 590 px within 0.3 s.
   - Why it matters: low. It is one hop in a 0.35 s move and not a layout failure. I did not see a flash in the captures I took at the transition frames.
   - Proposed fix: none needed now. If fixed with defect 1, the map cap also removes the tall first frame.

4. **Small, not new:** timeline pins overlap at 721 (`ch-her-spark-721x900-dark-m1.png`, 22 and 24, 4 and 6 at 960); the round 4 note about "Paused" and "Resumed" under "Before this moment" on dropped candidates is still there (`drop-her-spark-960x1080-light.png`).

## What I did not check

- Real iOS Safari, Android, Firefox, real touch and a real phone (viewports only).
- Real audio, a screen reader, 200 percent zoom, print.
- His Open page: opened only in the all-moments walks and the geometry compare (not in the screenshots).
- The first-screen Read layout at these sizes: I only used it to open a moment.
- The Play walk beyond about 78 s (moments 4, 7, 8) and at 1100 x 900 or 721 (I measured the walking boxes there, they equal the old ones).
- Window heights between 801 and 899 px at 721 to 960 px wide were sampled at 800 x 800 and 960 x 900 only. The cut starts somewhere between them.
- Contrast numbers and wording: Sasha's call. I did not check numbers against `findings.json` or read the code beyond the diff.
