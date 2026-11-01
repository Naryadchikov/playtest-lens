Reviewer: Grok 4.7 (xhigh), Cursor via T3. Commit 17a9675 (task 37, Claude Fable 5.1).

NOT PASS. 1 blocking finding.

## Blocking

1. `report/render.py:389` and `report/render.py:818` (same class at `report/render.py:392` and `report/render.py:801`, and at `report/render.py:399` and `report/render.py:857`). Class: decorative SVG geometry takes the click meant for a pin, so the pin opens the wrong moment or cannot be clicked.

   The focus ring is a circle of radius `pin radius + 14` (`PIN_R` 44, so 58), `fill: none`, `opacity: 0`, and it still participates in hit testing. The rank text is `pointer-events: none` (`report/render.py:390`), so the click has to land on the shape. On her Spark page the rank 4 pin and the rank 17 pin are 57.3 map pixels apart (`translate(907.6 1678.4)` and `translate(947.6 1637.4)`). Rank 17's ring passes through rank 4's center.

   Chromium and WebKit both refuse a real click on `#ovmap a.pin[data-open="f4"]`. Playwright's log: the locator resolves to `<a href="#m4" data-open="f4" ... aria-label="Moment 4, Confused, 3:52">`, then `<circle r="58" class="ring">` from `<a href="#m17" data-open="f23" ... aria-label="Moment 17, Confused, 14:23">` intercepts pointer events. A forced click at that point opens `#m17` with `.cur` on `f23`. Dispatching the click on the rank 4 element itself opens `#m4`. The handler is fine. The shape on top is wrong. Floor 1 of that overview has no pair this close. The same ring is drawn on both maps.

   Hollow pins miss for the same reason. `.pin.hollow use` is `fill: none` (`report/render.py:392`), and the ring is only a stroke, so the center is empty. On the ground floor, `elementFromPoint` at the center of the dropped pins `f13`, `f18`, `f26`, and `f32` hits the route polyline or the map picture. A click on `#ovmap a.pin[data-open="f13"]` times out in both browsers because `<polyline class="line">` is what the pointer hits. `tests/test_report.py:118` checks the `href` string and never clicks.

   In Watch the dot is painted after the pins (`report/render.py:857`, halo radius 46). With `#m4` open, the centers of the rank 16 and rank 17 pins hit `circle.halo`. Those clicks do not open a moment.

   Proposed fix: `pointer-events: none` on `.pin .ring`, `.route`, and `.dot`. Give every pin a transparent disc of its own radius (`fill="transparent"`, which is a hit target; `fill: none` is not) as the first child of the `<a>`, so a hollow pin and a pin under a neighbour's old ring both hit their own `<a>`. One rule covers the overview and Watch, because both call `_render_pins`.

## Smaller

1. `report/render.py:1411`. Class: a floor change inside the 30 s window deletes the earlier part of the strong trail instead of starting a new segment. `pts = []` on `q.floor !== i` drops points already collected. At map time 840 on her Spark page the shown floor is 0, 28 route points on that floor fall in `[810, 840]`, and the strong polyline has 7 points. The upper floor span 831.58 s to 833.09 s is what splits them. The faint route is still the whole floor. Proposed fix: when the floor does not match, draw the current run if it has two points, then start a new run.

2. `report/render.py:1340` and `report/render.py:1439`. Class: the line above the map omits the last game event once it is more than 60 s old. At map time 100 the "Before this moment" list shows the three events at 0:16 and `#lastev` is empty. At map time 200 the line shows the event at 3:19. Her Spark file has 7 gaps over 60 s, the longest 140.2 s. Proposed fix: always show the latest event at or before the map time. The time already says when it was.

3. `report/render.py:690`, `report/render.py:906`, and `report/render.py:1173`. Class: the header and the dropped counts are `len` of the rendered lists, not `summary.kept` and `summary.dropped`. Kind counts do read `summary.counts`, and the stuck time reads `summary.lost_s` (her Spark header is `5:42`, which is `int(342.49)`). On the four final files the list lengths equal those summary fields (24/4, 32/15, 13/5, 8/8). Setting `summary.kept` to 99 on the redesign fixture still prints `9 moments kept`. Pages with no summary, such as `tests/fixtures/findings_sample.json`, have no other count to print. Proposed fix: when `summary` is present, print `summary.kept` and `summary.dropped`.

4. `report/render.py:828`, `report/render.py:1042`, and `report/render.py:1127`. Class: visible words outside `LABELS`. The pin and the F9 line hardcode `F9`. The place-heading note builds `attempt` and `moment` with `_plural` (`1 attempt, 1 moment, ...` in `tests/test_report.py:376`). Proposed fix: put those words in `LABELS` and pluralise from there.

5. `report/render.py:1564`. Class: the `ended` handler does not remember which clip it belongs to. On WebKit, after Play had set `aria-pressed` to true on `#m4`, Next moved to `#m5` and a synthetic `ended` on the same element then set `travelling` to true, so the moment that just opened was left behind. Chromium's play flag was already false, so the same dispatch stayed on `#m5`. A real Next at `currentTime` 19.9 stayed on `#m5` with the travel overlay hidden, in both browsers, and Play the session still visited every unplanned moment (below). Proposed fix: ignore `ended`, `pause`, and `timeupdate` unless `video.currentSrc` is still the clip `showMoment` loaded.

## What held

`.venv/bin/python -m pytest -q --tb=line`: 237 passed, exit 0, 40.44 s. No model call.

Fresh render of her Spark findings matches `runs/final/cogito_person2-muse-spark-1.2-contributor-report.html` (`diff -q` exit 0). The four final pages each contain one `<script>` and one `</script>`. The only URL is `http://www.w3.org/2000/svg`. No `/Users/`, no user name, no token. Payloads `</script><script>alert(1)</script>`, `<!--`, and `<!--<img src=x onerror=alert(1)>-->` placed in the verdict, quotes, notes, labels, zones, and events are escaped, and the page still has one script tag. The four changed files have no em dash and no en dash.

`PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I /tmp/r23/probe.py` (Chromium and WebKit, her Spark page, clips symlinked beside `/tmp/r23/her.html`):

- One current moment. `#m1`, `#m13`, `#d-f13`, and `#d-f32` each open Watch with a single `data-open` on `.cur` (the pin and the timeline mark) and the file's summary in the caption. While the timeline is scrubbed, `.cur` is 0.
- Read and Watch are not both hit-testable. With Watch open, `elementFromPoint` at the top and the middle is inside `#watch`, `#read` is inert, and `aria-hidden` is true. After Back, the hits are `#read` and Watch is hidden.
- Back and Escape land on the same place. From the rank 24 still, both leave Watch hidden, clear the hash, focus `Watch moment 24`, and set `scrollY` to 5787 in Chromium and 5788 in WebKit. Escape with focus on `#clip` closes Watch.
- Play the session stops on the unplanned moments only. Boosting the travel clock and finishing each clip reaches `#m4 #m7 #m8 #m10 #m11 #m16 #m17 #m20 #m21`, then `End of the session`, in both browsers. The by-design moments are not in that list. Listeners for `timeupdate`, `seeked`, `play`, `pause`, `ended`, click, and `keydown` are added once at load. After Back the cursor stays at `100%` and Watch stays hidden.
- Previous and Next reach every kept moment. From `#m1`, Next produces `#m1` through `#m24` in order. Previous from the end clamps on `#m1`. ArrowRight and ArrowLeft do the same step.
- The floor follows the player. Opening `#m4` shows floor 0. A timeline click at 265 s shows floor 1. Choosing floor 0 holds through 300 s (the player is still on floor 1) and releases by 600 s, where floor 1 shows again.
- The Time spent control is the one `#heat` checkbox. Watch has 0 `.heat` groups. The overview heat group's display goes from `none` to `inline` when the box is checked. Problem links open the moment in the `href` (`data-open="f4"` opens `#m4`).
- The dot follows `clip.start_s + video.currentTime`. The watch polylines rebuild all 1250 route points. On `#m4` (`data-clip` 222 to 242), `currentTime` 0 puts the dot on the route point at 221.02 s, and `currentTime` about 10.3 puts it on the point at 232.1 s. The transform matches that point's pixels. f1, f16, and f31 show the file's summary, quote, `data-t`, floor, and `m:ss` in the row.
- No `pageerror` and no console error on the four final pages, either browser, in the 800 ms after load.

`test_play_stops_only_at_unplanned_moments` checks `data-stop` and that the script source contains `stops` and `showMoment(kept[i], S.playing)`. It does not run the script. The run above is what covers that behaviour.

## What I did not check

I did not judge the look or the wording. I did not run Firefox, Safari, VoiceOver, print, or 200 percent zoom. I did not play a clip through at 1x. The Play probe seeks each clip to its end. I did not click pins on the other three final pages. The renderer is the same one. I did not press Escape from inside the browser's media-control shadow UI. Escape from the `#clip` element itself closes Watch. I did not read held-out notes, `runs/costs.jsonl`, or the Keychain. I did not review `godot/`, `game/`, or the analyzer prompts. `analyzer/spatial.py` and `analyzer/findings.py` are not in this commit.
