Reviewer: Grok 4.7 (xhigh), Cursor via T3. Round 2. Commit 952ecb1 (task 38, Claude Fable 5.1).

**PASS.**

No blocking finding. One smaller finding: a synthetic `ended` after Next still starts the walk (review 23, smaller 5). A real Next near the end of a clip stays on the new moment, in both browsers.

Checked `git diff 17a9675 952ecb1` for `report/render.py`, `tests/test_report.py`, `tests/test_spatial.py`, and `docs/design/UX_PASS.md`. The code change is commit 952ecb1. `ded2110` only adds the round-1 reports and the brief.

## Review 23

1. **Pins take the wrong click. Fixed.** `report/render.py:404` sets `pointer-events: none` on `.route`, `.strong`, `.dot`, `.heat`, `.pin .ring`, and `.pin .edge-mark`. `report/render.py:851` puts a `<circle class="hit">` of the pin's own radius first inside the `<a>`, with `fill: transparent` (`report/render.py:405`). The same `_pin_open` draws the overview and Watch.

   `PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I /tmp/r25/probe.py`, her Spark page rendered to `/tmp/r25/her.html`, real `locator.click` (no force), Chromium and WebKit:

   - Overview floor 0: 22 of 22 pins, including the 57.3 px pair `f4` (`#m4`) and `f23` (`#m17`) and the hollow pins `f13`, `f18`, `f26`, `f32`. Each hash matched that pin's `href`.
   - Overview floor 1: 6 of 6.
   - Watch, moment 4 open: `elementFromPoint` at the centers of rank 4 (`f4`), rank 16 (`f22`), and rank 17 (`f23`) hit `use` inside that pin. The ring and the halo were not the hit. The dot's computed `pointer-events` is `none`. A mouse click at the dot's center hit `f23` and opened `#m17`. Then all 28 Watch pins, after showing that pin's floor, opened their own `href`.

   No click timed out. No `pageerror` and no console error on the four final pages, either browser, in the 800 ms after load. No request to `http:` or `https:`.

2. **Trail across a floor change. Fixed.** `report/render.py:1482` pushes the current run before starting another when `q.floor !== i`. On her page the ground-floor window around 840 s is split by the upper floor at 831.58 s to 832.59 s. A timeline click that landed at 846.2 s (floor 0) drew two strong polylines, 15 points and 13 points, in both browsers (`/tmp/r25/probe2.py`). An earlier click at 832.0 s was the upstairs span, so floor 0's trail was empty there. That click was the wrong time, not a one-run trail.

3. **Latest event however old. Fixed.** `report/render.py:1516` shows the latest event at or before the map time with no 60 s cutoff. `EVENT_FRESH` is gone. At map time 100.9 s, `#lastev` reads `0:16` plus the event at 16.58 s. The next event is at 156.81 s, so the gap is 83 s. Both browsers.

4. **Counts from `summary.kept` and `summary.dropped`. Fixed.** `report/render.py:704` (`_counts`) uses those fields when the summary has them, and the list lengths otherwise. Her header is `21:20 recording, 24 moments kept, 4 dropped. 5:42 stuck or blocked.`, and `a[href="#dropped"]` appears twice (header and legend). `tests/test_report.py` sets `summary.kept` to 99 and `summary.dropped` to 7 and expects those numbers. That test fails on `17a9675`.

5. **Visible words through `LABELS`. Fixed.** `attempt`, `visit`, `moment`, `{n} dropped`, and `F9` live in `LABELS["words"]` (`report/render.py:80`). The problems line, the group note, the pin text, the F9 line, and the dropped link read them. `test_visible_words_come_from_labels` swaps the dict for `try`, `stop`, `beat`, `{n} out`, and `KEY`, and the page follows. That test fails on `17a9675`.

6. **Clip events only for the loaded clip. Not fully fixed.** See the smaller finding below. `timeupdate` does follow the loaded clip: with `#m4` open, `currentSrc` equals `new URL(still src).href` (`file:///tmp/r25/lobby-player-1-clips/c00232.00.mp4`), and a `timeupdate` at `currentTime` 5 moves the cursor from `17.33%` to `17.72%` and moves the dot. Both browsers.

## Review 24, the code side

- **Space in Watch. Fixed.** `openWatch` focuses `#play` (`report/render.py:1554`). The key handler still skips Space on a button (`report/render.py:1699`), so Space activates Play once. After opening the first problem, focus is `#play`, `aria-pressed` is `true` (the clip is playing), one Space sets it to `false` and leaves Watch open, a second read 250 ms later is still `false`, and a second Space returns it to `true`. Chromium and WebKit.
- **Back restores the opener's place and focus. Fixed.** `report/render.py:1565` treats an opener in `#read` that is outside `article.m` and `article.d` as the first screen: `scrollTo` the saved `scrollY`, then focus the opener. From the Archive problem, Escape leaves `scrollY` at 0 and focuses the place link (`data-open="f4"`). The moment row is at document y 1832. From a badge, Back restores `scrollY` 80 and focuses that badge. From the `f4` map pin, Back restores `scrollY` 0 and focuses the SVG `<a>`. From moment 20's still, Back leaves `scrollY` at 5072, keeps the row in view, and focuses its Watch button. Both browsers.
- **Off-map pin. Fixed.** `report/render.py:832` clamps a point outside the viewBox to `radius + 8` and marks it. His rank 8 pin (`f16`, Laboratory) renders at `translate(52.0 817.3)` in a 1334 by 2048 viewBox, with `circle.edge-mark` and `circle.hit`, and the name ends in `outside the mapped area`. At clip open the player line is `Archive, Ground floor` (the route point at clip start, 483 s, is on the map) and `#offmap` is visible: `This moment is outside the mapped area. Its pin sits at the map's edge.` Seeking the clip to 10 s sets the map time to 493 s, the moment's own time, and the player line becomes `Outside the mapped area, Ground floor`, with the note still visible. Both browsers.
- **`{n} dropped` scrolls and does not open Watch. Fixed.** From `scrollY` 0 the header link sets the hash to `#dropped`, leaves Watch hidden, and scrolls to the maximum, `scrollY` 6114. The heading sits 279 px down because that is as far as the page can scroll (the section is shorter than the 1080 px viewport).
- **Walk column and the stale frame. Fixed.** The click on Play the session returns with the caption heading `Up next`, `#clip.controls` false, the travel overlay shown, and the clock already `0:16`. `startTravel` calls `drawTravel` before the animation frame (`report/render.py:1602`).
- **Next stays in the dropped list. Fixed.** On a fresh load, Next from `f13` goes from `Dropped 1 of 4` to `Dropped 2 of 4` and `#d-f18`. Both browsers. An earlier WebKit read of `#m5` was the synthetic `ended` below, still walking, between two separate reads. One evaluate on a fresh page does not do that.
- **Play and Pause contrast. Fixed.** `report/render.py:370` sets `background: var(--accent)` and `color: var(--on-accent)` on `.bar .nav .primary`, after the sunk nav rule. Computed contrast, visible label on the button background: light 7.51:1, dark 7.88:1, Play and Pause, both browsers.
- **400 px axis. Fixed.** `report/render.py:464` hides even labels under 720 px. At 400 px, 6 of 11 labels are visible (`0:00`, `4:00`, `8:00`, `12:00`, `16:00`, `20:00`) and no pair overlaps by more than 2 px. Both browsers.

## Smaller

1. `report/render.py:1648` and `report/render.py:1662`. Class: `loadedClip` treats `currentSrc` as the clip identity, and Next has already selected the new clip before a late `ended` can arrive, so the event starts the walk for the moment that just opened.

   `loadedClip` requires `video.currentSrc === new URL(S.cur.src, location.href).href`. On Next from `#m4` to `#m5` the click itself logs `play` and `loadeddata` for `c00248.00.mp4`, and `currentSrc` already matches `#m5`. `aria-pressed` stays `true` because that `play` event passes `loadedClip` and sets the flag (`report/render.py:1657`). A synthetic `ended` then takes the `S.playing` branch and sets `travelling`. Observed in both browsers, including after a real seek to 19.8 s of the 20 s clip: the real Next stays on `#m5` with the travel overlay hidden (the media events are `emptied` and `play`, and `video.ended` is false), and the synthetic `ended` then sets `travelling` with `video.ended` still false and `currentTime` 0.

   Round 1 saw this synthetic dispatch fail on WebKit only, because Chromium's flag was already false. The new `play` handler sets the flag again, so Chromium now takes the same path.

   A real Next at 19.8 s does not fire `ended` and does not leave `#m5`. The user-visible path from review 23 holds. The guard does not.

   Proposed fix: in the `ended` listener, return unless `video.ended` is true. A real end sets that flag before the event. The synthetic event does not, and a clip that has just loaded is at `currentTime` 0 with `ended` false. Keep the `currentSrc` check for `timeupdate` and `pause`.

## Checks

`.venv/bin/python -m pytest -q --tb=line`: 245 passed, exit 0, 41.89 s. No model call from this review.

The new and updated tests against `git show 17a9675:report/render.py` (loaded from `/tmp/r25/oldtree`, `report.render.__file__` confirmed): 11 failed, exit 1, 0.15 s. That set is the pin hit rule, the Play contrast rule, summary counts, `LABELS` words, the clamped pin, the script rules for the trail, the latest event, and `loadedClip`, the narrow axis, the model line, the header link, `showMoment(list[i])`, and `test_enriched_file_loads_and_renders`.

In-memory render with a model name, `summary.kept`, and `summary.dropped` set to strings containing `<script>alert(1)</script>` and `<img ...>`: one `<script>` tag, and the payloads appear only as `&lt;script&gt;` and `&lt;img`. The four pages at `/tmp/r25/*.html` contain no `/Users/`. `git diff 17a9675 952ecb1` for the four code and design files contains no em dash and no en dash. The only URL in the renderer is `http://www.w3.org/2000/svg`.

## What I did not check

I did not judge the look or the wording. I did not run Firefox, Safari, VoiceOver, print, or 200 percent zoom. I did not play a clip through at 1x. The near-end Next seeks to 19.8 s and then presses Next. I did not click every pin on the other three final pages. I loaded each of them: no console error and no page error. I did not read held-out notes, `runs/costs.jsonl`, or the Keychain. I did not review `godot/`, `game/`, or the analyzer prompts. Nothing from `runs/` or `recordings/` was copied into a tracked file.
