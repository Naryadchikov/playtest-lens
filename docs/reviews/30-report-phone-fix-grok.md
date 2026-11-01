Reviewer: Grok 4.7 (xhigh), Cursor via T3. Commit b24db37 (Claude Opus 5.5).

**PASS.**

`runs/final/*-report.html` had been rendered again after b24db37 (they contain `grid-area: cap`, which is not in this commit). The checks used pages rendered from `git show b24db37:report/render.py` into `/tmp/r30/pages/`, with `MAPS_DIR` pointed at `report/maps` and the clip directories symlinked. Nothing from `runs/` was copied into a tracked file. `git diff a84618f b24db37 -- report/render.py` has no em dash and no en dash.

Chromium 156.0.8078.4 and WebKit 27.2, `PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I /tmp/r30/check.py` and `/tmp/r30/spot.py`, `prefers-reduced-motion: reduce`, light scheme, scale 1. All four sessions. 600 and 720 were 900 px tall. The wide script aborted media requests. A second pass on her Spark page loaded the real clips.

## What held

1. **On a phone the clip, the caption, and the map column stack, and the quote is the hit target.** At 360 x 640, 390 x 700, 400 x 860, 600 x 900, and 720 x 900, at a moment and while the session walks, every page in both browsers: clip/caption overlap 0, clip/map overlap 0, caption/map overlap 0, gap under the clip 12 px, gap under the caption 16 px. `.main` is `block`. Watch's width equals the viewport. No box sticks out of it.

   Her open page at 390 x 700, both browsers, same rectangles: clip top 64, bottom 265.4 (358 x 201.4). Caption top 277.4. Map column top 481.4. `elementFromPoint` on the quote at 25, 50, and 75 percent of its width returns the quote. While walking, the same gaps, `travelling` set, and the quote hits the same three points. At 360 the bar is 360 x 52. Back, Previous, Pause, and Next are one line (36.5 px). Next's right edge is 355.5. `scrollWidth` equals `clientWidth`, and the buttons do not overlap. `report/render.py:463` in b24db37 (`.main` and `.watch.travelling .main` are `display: block`; `.screen` is a column flex; the clip is `width: 100%`). `report/render.py:364` pins Watch to one `minmax(0, 1fr)` column. `report/render.py:371` keeps the bar buttons on one line.

2. **At the laptop sizes the caption's height equals its scroll height.** 1280 x 720, 1366 x 768, 1440 x 900, 1536 x 864, and 1920 x 1080, every kept moment and every dropped candidate, all four pages, both browsers: `clientHeight` equals `scrollHeight` and no child sticks out of the caption. The tallest measured box is 212 / 212 (`overflow: auto`). The clip at 1280 x 720 is 547.5 x 308, at 1440 x 900 is 867.5 x 488, and at 1920 x 1080 is 1187.5 x 668, which is `(100vh - 52px - 104px - 256px)` by 16:9 (`report/render.py:377`).

   At 960 x 1080 the moment columns are `651.422px 260.578px` (ratio 2.5). The clip is 651.4 x 366.4. The caption is 522 / 522. A timeline walk is `304px 608px` (ratio 0.5) on his open page, and the same 0.5 ratio on the other three from Play the session. At 1920 x 1080 that walk is `616px 1232px`. The quote hits on the 960 moment and on the her Spark walk.

3. **The latest game event is only in the line above the map.** The page clock (`#cursor`) is the map time. Both browsers, problems none, and the latest item's label is not repeated in the list:

   - Her Spark, moment 1, map time 29 s: the line holds the latest event, the list holds the 2 events before it, and "No game events yet." is hidden.
   - A timeline click near 0 s (map time 1 s and 0.4 s): the line is empty, the list is empty, and "No game events yet." is shown.
   - His open page, moment 1, map time 20.8 s, which is before every event: the same empty state.
   - A late moment and a walk (her moment 20 at 1122 s, his moment 8 at 483 s, his open moment 13 at 486.2 s): the line holds the latest, the list holds 4 earlier events (`EVENTS_SHOWN`), and the empty state is hidden.

   Every event's last child is a text node, so the line copies the label (`report/render.py:1524` in b24db37). `.events li.last` is gone with the class toggle.

4. **Tests and a real clip load.** `.venv/bin/python -m pytest -q`: 245 passed, exit 0, 46.60 s. No model call from this review. `runs/costs.jsonl` sums to 0 across 1346 lines. Her Spark page at 390 x 700 with the clips allowed to load: 0 page errors and 0 console errors, both browsers, after opening moment 1.

## Nit

**The 420 px button padding does not apply.** `report/render.py:480` sets `.bar button { padding: .4em .6em }`, specificity (0, 1, 1). `.bar .back` and `.bar .nav button` set padding at (0, 2, 1), so they win. At 360, computed padding is `6px 13.5px` on Previous, Pause, and Next, and `6px 13.5px 6px 10.5px` on Back (the `.9em` / `.7em` rules). The bar's own padding and gap do shrink (`0px 8px`, gap `8px`). The bar still fits, with Next 4.5 px inside the right edge.

Proposed fix: under 420 px, set the padding on `.bar .back, .bar .nav button`.

## What I did not check

I did not judge the wording or the look. I did not run Firefox, iOS Safari, a real phone, VoiceOver, print, or 200 percent zoom. I did not play a clip through at 1x. I did not review `godot/`, `game/`, the analyzer prompts, or commit 5d7400a. I did not read held-out notes or the Keychain.

Play the session on his open page opens moment 1 with the moment columns (ratio 2 at 1280, 2.5 at 960) rather than the walking columns. `startTravel` (`report/render.py:1612` in b24db37) is unchanged in this diff: when the next stop's clip starts at or before the first route point, Play shows that moment. A timeline walk on that page does use the walking columns. That behavior is outside this commit.
