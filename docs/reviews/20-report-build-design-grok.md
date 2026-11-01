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

## Round 2

Reviewer: Grok 4.7 (xhigh) through Cursor, in T3 Code. Commit 5b2c281.

PASS.

## Checks

`.venv/bin/python -m pytest -q --tb=line`: 237 passed, exit code 0, 44.34s. The suite finished with no API key in the environment.

Rendered `runs/check/person2-findings.json` to `/tmp/review20r2.html`.

The heat rule reaches the timeline. The rendered page has two `:has(.view-heat:checked)` rules that name `.timeline`, and both selectors are `.page:has(.view-heat:checked) .timeline`. One sets `visibility: hidden` (`report/render.py:475`). The other, inside `max-width: 1100px`, sets `display: none` (`report/render.py:564`). `section.timeline` sits after `</aside>`, and the markup after `</section>` is the page's closing `</div>`. `.focus` and `.readout` sit inside the pane, where the pane rule still hides them. In Chromium, with the heat radio checked, both selectors match the timeline element. At 1920 x 1080 the computed visibility is hidden and display stays grid: `elementFromPoint` misses the bar, and a click on its box leaves `data-mode` at heat. At 960 x 1080 the computed display is none and the box height is 0. Commit 6847e40 still has `.pane:has(.view-heat:checked) :is(.timeline, .focus, .readout)` and has no `.page` timeline rule, so `test_the_heat_view_reaches_the_timeline_outside_the_pane` fails on that source.

`_event_icon` is defined once (`report/render.py:1347`). Commit 6847e40 defines it twice.

A floor change stays in the route. `_downsample` (`analyzer/spatial.py:271`) drops a middle sample when it is under `ROUTE_MIN_STEP_S` from the last kept sample and the floor is the same, and drops the sample before the last when that sample is under `ROUTE_MIN_STEP_S` from the last and its floor equals the one before it. A floor change fails both conditions. `route.points` and `floor_spans` are built from the same `route_samples` list (`analyzer/spatial.py:631`): paused positions never enter it, and the scene filter and the flash-time filter run before both. The review input (t=0 floor 0, t=0.5 floor 1, t=1.0 floor 0) keeps three points. The previous function keeps floors `[0, 0]`, so `test_downsample_keeps_the_sample_where_the_floor_changes` fails on it. 400 random sequences of length 1 to 11, and every floor pattern of length 1 to 7 at 0.4 s steps, left 0 spans without a point. A fresh `enrich` of this session's log matches the file: 1250 route points, 9 spans, 0 spans without a point.

The findings file stays the source of the page. The new page code picks the overview clip from an existing finding, fills the dropped counter from the rendered dropped rows, and places the dot tag from the map viewBox. The tiles read `summary.kept` and `summary.dropped` (24 and 5). `_event_label` (`analyzer/spatial.py:579`) reads the log line's path, open or locked flag, quest, step, and item, and fills the fixed templates. The same fresh `enrich` matches all 58 event labels. `test_node_names_become_words`, `test_door_and_lock_labels_name_the_thing_and_its_room`, and the updated expectations in `test_events_and_zones_are_written_in_video_time` cover the rule. Those expectations fail on the previous function, which wrote the raw path.

The page matches the file. `random.Random(35)` picked f24 at 906.0 s (floor 0), f11 at 377.0 s (floor 0), and f5 at 248.0 s (floor 0): summary, quote, checker note, `data-t`, m:ss, and floor match. All 24 kept findings have `data-t` equal to `time_s` and an `id="m<rank>"` anchor. All 6 with a floor above 0 show that floor's name. All 5 dropped findings have a note, and each note is the reason on its row.

Escaping holds. 28 file strings that contain `&`, `<`, `>`, a quote, or an apostrophe do not appear raw, including inside the one `<script>`. The 58 event labels contain none of those characters and no slash. A fixture payload `</script><script>alert(1)</script>"'` in the summary, quote, checker note, game state, and an event label is escaped. The raw payload is absent, and the page still has one script tag.

The diff from 6847e40 to 5b2c281 in `analyzer/`, `report/`, `tests/`, and `docs/design/` has no em dash, no en dash, no key or token pattern, and no `selftest`, `window.DATA`, `shot=`, `#sim`, or `&shot`. `analyzer/analyze.py` returns before the candidate pass when the log has no `sync_flash` line, the same condition `analyzer/check.py` already uses.

Chromium kept the chosen moment through the page's own scroll: the first problem (`#m11`) stayed current from scroll 0 to 5559 px, the last dropped mark (`#d-f32`) stayed current through the rest of the scroll, Overview returned to the top in whole mode, and a timeline click after moment 1 cleared the stage clip (`data-mode` session, no src, no controls). No page errors.

## Blocking

None.

## Nits

None.

## What I did not check

I did not judge the look or the wording. I did not render the open-weights findings file. I did not read held-out notes, watch the recording, or read `runs/costs.jsonl`. I did not review `godot/`, `game/`, or `analyzer/spark_test.py`. I did not run WebKit, Safari, or the print stylesheet as the active medium, and I did not play a clip or run a full session. The browser check was Chromium: heat hit-testing at 1920 x 1080 and 960 x 1080, one problem jump, the last dropped mark, Overview, and one timeline scrub.
