Reviewer: Grok 4.7 (xhigh) through Cursor, in T3 Code. Commits c1cd19c, 6847e40.

NOT PASS. 1 blocking finding.

## Checks

`.venv/bin/python -m pytest -q --tb=no`: 224 passed, exit code 0, 54.80s. No model call.

Rendered `runs/check/person2-findings.json` to `/tmp/review20.html`. 24 kept anchors (`#m<rank>`), 5 dropped articles, each with its reason. `random.Random(20)` picked f31 at 1219.0 s (floor 0), f29 at 1204.0 s (floor 0), and f5 at 248.0 s (floor 0): summary, quote, checker note, `data-t`, m:ss, and floor match the file. All 6 kept findings on floor 1 show `data-floor="1"` and "Upper floor". 28 file strings that contain `&`, `<`, `>`, a quote, or an apostrophe do not appear raw. A fixture payload `</script><script>alert(1)</script>"'` in the note, game state, quote, summary, area, puzzle, recording, id, event label, zone, verdict, and problem place is escaped (17 times); the page has one `<script>` and the raw payload is absent. No `selftest`, `&shot`, `#sim`, `shot=`, or `window.DATA`.

The page reads floors, heat, `lost_s`, kind counts, and `summary.problems` from the file. It formats stored endpoints (`_mss`, `_span`, `_duration` of `end_s - time_s`), maps world points with each floor's JSON, stacks marks, and picks the current moment. Playback time is `clip.start_s + video.currentTime` or the session clock, and the dot snaps to an existing route point. `len` of a rendered list (problem moments, dropped rows, attempts in a group) is a label; on this file `summary.kept` is 24 and `summary.dropped` is 5, matching those lists.

Spatial, checked against the log and with small inputs: 1247/1247 route points match an independent floor from `y` and `y_floor_min` 2.4. A null `y` and `y` 2.399 stay on floor 0; `y` 2.4 is floor 1. The Laboratory map has `y_cutoff` 2.4 and no `y_floor_min`: one floor, and samples at `y` 0.2, 5.0, and null are all floor 0. Heat stays per floor (6 spots and 3 on this file; a shared x,z on both floors stays two spots). Pins: 23 and 6, 0 pairs under 55 px on the same floor, same x,z on two floors unmoved. Independent union of stuck and blocked visit spans is 342.49, matching `summary.lost_s`. 4 problems match that order, friction, `lost_s`, and moment ids. A kept finding with no beat is left out of problems; with `end_s` it still counts in `lost_s`. f10 at 327.0 s has a zero-length visit and no `end_s`, so it adds 0. No kept finding lacks a beat (5 dropped ones do). No em dash, en dash, key, token, or recording in the scoped diff.

## Blocking

1. `report/render.py:458`. Class: the heat-map rule does not match the timeline, so the timeline view stays on.
   The rule is `.pane:has(.view-heat:checked) :is(.timeline, .focus, .readout)`. The space before `:is` is a descendant combinator. `section.timeline` is written after the pane (`report/render.py:2320` then `report/render.py:2321`). In `/tmp/review20.html` the timeline markup is outside `<aside class="pane">`. `.focus` and `.readout` sit inside the pane, so those parts of the same rule can apply; `.timeline` cannot.
   With the heat radio checked, the route and pins hide (`.trail-layer` is inside the pane, `report/render.py:456`) and the heat blobs show. The timeline bar stays visible. A click or drag on it calls `toSession` (`report/render.py:2165`), which calls `showTrail` (`report/render.py:2026`) and checks the Timeline radio (`report/render.py:2001`). Sasha, 2026-10-28: the heat map turns the timeline view off and is only the heat map. The heat note says the same (`report/render.py:217`). `tests/test_report.py:458` asserts the trail-layer string only, so this still passes.

## Nits

1. `report/render.py:1278` (repeated at `report/render.py:1320`). Class: dead duplicate.
   `_event_icon` is defined twice with the same body. The second definition replaces the first. Callers hit the second. The first is unused.

2. `analyzer/spatial.py:243`. Class: a floor change inside the route step is missing from `route.points` while `floor_spans` keeps it.
   `_downsample` drops a middle sample closer than `ROUTE_MIN_STEP_S` (1 s) to the last kept sample. `_floor_spans` (`analyzer/spatial.py:225`) uses every sample. Input: t=0 floor 0, t=0.5 floor 1, t=1.0 floor 0. Points are floors `[0, 0]`. Spans include floor 1 from 0.5 to 1.0, so the upper-floor bar has no route point. On this session, 0 of 9 spans lacked a point.

## What I did not check

I did not judge the look or the wording. I did not open a browser, play a clip, or toggle the heat radio; the blocking finding is the selector against the markup. I did not render the open-weights findings file. I did not read held-out notes, watch the recording, or read `runs/costs.jsonl`. I did not review `godot/`, `analyzer/analyze.py`, or `analyzer/spark_test.py`. I did not touch `game/`.
