Reviewer: Grok 4.7 (xhigh), Cursor via T3. Commit a84618f (Claude Opus 5.5).

**NOT PASS.** 1 blocking finding.

HEAD is now b24db37, and `runs/final/*-report.html` matches that later render. The checks below used pages rendered from `git show a84618f:report/render.py` into `/tmp/r27/pages/` (clips symlinked, maps read from `report/maps`). Nothing from `runs/` was copied into a tracked file.

## Blocking

1. **On a phone the caption grows, and its top sits under the clip, so the quote is covered.** Class: the 720px screen is two `auto` grid rows, and the clip's height comes from `aspect-ratio` while its width is `100%` of that grid area, so the row is shorter than the clip box and the caption track starts inside the picture.

   `report/render.py:465` sets `.screen { grid-template-rows: auto auto; }` and `report/render.py:466` sets `.caption { overflow: visible; }`. The clip width is `min(100%, calc((100vh - var(--bar-h) - var(--tl-h) - 200px) * 16 / 9))` (`report/render.py:376` in that commit).

   `PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I` against `/tmp/r27/pages/her-spark.html`, moment `m24`, `prefers-reduced-motion: reduce`, Chromium and WebKit (same rectangles):

   - 400 x 860: clip box top 64, bottom 271 (207 px). Caption top 113, bottom 396 (283 px). Overlap 158 px. `scrollHeight` 283 equals `clientHeight` 283, `overflow-y` is `visible`, document `scrollWidth` 400 equals `clientWidth`. Quote top 145 to 235, summary top 243 to 293, head top 113 to 137. `elementFromPoint` on those three hits `#clip` (Chromium). The cause, at top 301, is below the clip.
   - 390 x 700: clip bottom 265 (201 px), caption top 76 (283 px). Overlap 189 px. Same scroll and overflow result, document width 390. Quote top 108 to 198 and summary top 206 to 256 hit `#clip`. The caption background is `rgba(0, 0, 0, 0)`.
   - 1440 x 900: clip bottom 581, caption top 593. No overlap.

   The words are in the caption box, and that box does not scroll, which is the measurement the phone fix asked for. The quote is still hidden, under the video, and scrolling `.main` moves the clip and the caption together.

   Proposed fix: under 720 px, lay `.screen` out in normal flow (a column flex, or block) so the caption's top is the clip's bottom. Keep `.caption { overflow: visible }` and `.main { overflow: auto }`.

## What held

`git diff 952ecb1 a84618f -- report/render.py`. The code change is that file. The same commit adds the round-2 review writeups. `git diff 952ecb1 a84618f -- report/render.py` has no em dash and no en dash.

- **Ended guard.** `report/render.py:1674` returns unless `video.ended` and `loadedClip()`. After Next from moment 1 to moment 2, `currentSrc` matched the new clip, `aria-pressed` was `true`, `video.ended` was false, and a synthetic `ended` left the hash on `#m2` with the travel overlay hidden. Both browsers. During Play the session, a capture-phase listener on the real `ended` of `c00232.00.mp4` saw `video.ended` true at `currentTime` 20, hash `#m4`, not yet travelling. After the page handler, Watch was travelling, the overlay was shown, and the counter read `Walking to the next unplanned moment`. Both browsers.
- **Previous and Next.** On her Spark page, 24 kept and 4 dropped. Moment 1 of 24: Previous disabled (opacity 0.4), a click stays on `#m1`. Moment 2 of 24: both enabled (opacity 1). Moment 24 of 24: Next disabled, a click stays. Moment 23: Next enabled again. Dropped 1 of 4: Previous disabled. Next goes to Dropped 2 of 4 (`#d-f18`). Dropped 4 of 4: Next disabled. Play stays enabled. From the first moment, a timeline click sets the counter to `Walking to the next unplanned moment` and enables both buttons. A walk started from the dropped list does the same, and the line above the map is the room at that time (`Archive, Ground floor`). Both browsers. `report/render.py:1552` and `report/render.py:1609`.
- **Place line.** His moment 8: the line is `Laboratory, Ground floor` (the moment's `data-place`). The route at clip start, 483 s, is `Archive, Ground floor`. Seeking to 10 s moves the dot from `translate(892.8 1648.9)` to `translate(-7.6 817.3)` and the route name becomes `Outside the mapped area, Ground floor`. The line stays `Laboratory, Ground floor`. A paused walk at 483 s says `Archive, Ground floor`, and the Up next caption carries `Laboratory, Ground floor`. A second walk time, 118.68 s, says `Between rooms, Upper floor`. Her moment 1 at the clip's first second says `Lobby, Ground floor` while that map time is between rooms. `report/render.py:1509`. At a moment the caption head does not repeat the place (`capPlace` empty). The place span is added only for the Up next preview (`report/render.py:1547`).
- **1100 px columns,** settled with reduced motion, her page, both browsers. At a moment: 1920 and 1440 are `1232px 616px` and `912px 456px` (ratio 2, the 2fr 1fr rule). 1000 is `680px 272px` (ratio 2.5, the 5fr 2fr rule). Walking: 1920, 1440, and 1000 are ratio 0.5 (`616px 1232px`, `456px 912px`, `317px 635px`), so `.watch.travelling .main` still wins under 1100 px. At 400 the walking column is one track, `368px`.
- **Badge digits.** Light: white on `rgb(148, 98, 0)`, contrast 5.24, her page, 30 `.mk.k-confused b` and 18 `.tm.k-confused b`, Watch closed and open, both browsers. Dark: `rgb(27, 19, 0)` on `rgb(242, 193, 78)`, contrast 10.98, his page, 8 marks and 5 timeline digits, same. `report/render.py:251`, `report/render.py:445`, and the dark override at `report/render.py:220`.
- **Loads.** All four rendered pages, both browsers: no page error, no console error, no request to `http:` or `https:`.
- **Tests.** `.venv/bin/python -I /tmp/r27/pytest_commit.py` loads `report.render` from `/tmp/r27/render_a84618f.py` (`git show a84618f:report/render.py`, `MAPS_DIR` pointed at `report/maps`): 245 passed, exit 0, 42.69 s. No model call from this review. The suite does not assert the `video.ended` guard. The browser check above is the evidence for it.

## What I did not check

I did not judge the wording or the look past the checks above. I did not run Firefox, Safari, VoiceOver, print, or 200 percent zoom. I did not play a clip through at 1x. The real end seeks to the last 0.05 s of the first stop's clip (`m4`, `c00232.00.mp4`). I did not review `b24db37`, `godot/`, `game/`, or the analyzer prompts. I did not read held-out notes, `runs/costs.jsonl` beyond a cost sum of 0 across 1346 lines, or the Keychain.
