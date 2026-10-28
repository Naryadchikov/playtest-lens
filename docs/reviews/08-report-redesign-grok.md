Reviewer: Grok 4.7 (xhigh, fast) through Cursor in T3 Code. Commit bde28c2.

NOT PASS (3 blocking)

## Blocking

1. `report/render.py:353` and `report/render.py:378`. Class: a string from the file is written into HTML without escaping.
   `_render_header` puts `session.id` into the heading with `str.format` and writes that string in `<h1>`. The document `<title>` at `report/render.py:968` escapes the same id. The previous renderer escaped the id in the h1.
   Input: `session.id` set to `</h1><img src=x onerror=alert(1)>`. `findings.load` accepts it, because the id is a string.
   Result: `<h1>Session </h1><img src=x onerror=alert(1)>: Player 2</h1>`. The same file with `session.id` of `<script>alert(1)</script>` emits that script element in the h1. The title shows `&lt;script&gt;`. A sweep of player, level, recording, recorded, verdict, place, player label, summary, quote, game_state, check note, friction, resolved, beat area, puzzle, zone, clip path, and marker moment came out escaped. `test_every_string_from_the_file_is_escaped` never sets `session.id`, so the suite stays green.

2. `report/render.py:836`, `report/render.py:841`, and `report/render.py:887`. Class: a stored time of 0 is treated as missing, so the page shows another time.
   `_group_span` uses `attempt_start_s or time_s` and `attempt_end_s or end_s or time_s`. When `attempt_end_s` is null, the attempt heading uses `end_s or time_s`.
   Input A: the first kept finding of `tests/fixtures/findings_redesign.json` (attempt 2), with `attempt_start_s` 0, `attempt_end_s` 90, `time_s` 12, `end_s` 20, and the other findings removed.
   Result A: the heading is `Attempt 2 (0:00-1:30)` and the group note is `1 attempt, 1 moment, 0:12-1:30`. The note start is `time_s`.
   Input B: same finding, `attempt_start_s` 5, `attempt_end_s` 0, `time_s` 5, `end_s` 40.
   Result B: heading `Attempt 2 (0:05-0:00)`, note `1 attempt, 1 moment, 0:05-0:40`. The note end is `end_s`.
   Input C: `attempt` 1, `attempt_start_s` 10, `attempt_end_s` null, `time_s` 15, `end_s` 0.
   Result C: heading and note are `0:10-0:15`. The heading uses `time_s` because `end_s` is 0.
   `resolved_after_s` of 0 renders `Resolved after 0:00` (the `is not None` check at line 672). No test uses an attempt time of 0.

3. `report/render.py:881`. Class: a sort that changes the file's rank order.
   Inside an attempt, cards are sorted by `(time_s, rank)`. The brief says the page's order follows `rank` and `beat`. The design notes say cards are sorted by `time_s`. The brief wins. Attempts stay in attempt-number order, and the pin list stays in rank order. Line 892 sorts by rank only when `attempt` is null. The docstring at lines 6-7 says card order comes from rank and beat.
   Input: `tests/fixtures/findings_redesign.json`. North attempt 1 is rank 9 at 192s and rank 2 at 200s. South attempt 1 is rank 6 at 670s and rank 4 at 740s. Reversing the findings array leaves this order.
   Result: card ids `9, 2, 1, 3, 7, 6, 4, 5, 8`. Rank order inside those two attempts is 2 then 9, and 4 then 6. `test_groups_and_cards_follow_beat_and_rank` expects the time order, so the suite stays green.

## Non-blocking nits

1. `report/render.py:725`, `report/render.py:435`, `report/render.py:449`, `report/render.py:859`, `report/render.py:864`, and `report/render.py:916`. Class: a number computed from the file rather than copied from a field.
   Finding f1 (`time_s` 345, `end_s` 430) shows `(1:25)`, which is `end_s - time_s`. The across line uses `len(players)` (`3 of 3`, `2 of 3`). Player 2 on the plates shows `Player 2: 3 moments` and leaves `worst_t` 85 off the chip. The north group note says `3 attempts, 5 moments`. The dropped heading uses `len(dropped)`. The summary tiles do follow the file: `summary.lost_s` of 61 renders `1:01`, and the kind counts are `summary.counts`. These labels are the ones drawn on the mockup. The blocking case for order is finding 3.

2. `report/render.py:609`. Class: a placeholder for a missing optional field.
   Input: delete `session.level` and keep `route`.
   Result: the Level row in the header is absent. The image alt is `Top-down plan of the level level. ...` and the svg title is `Route and pins on the level map`.

3. `report/render.py:935`. Class: dropped findings are reordered.
   Input: the three dropped rows reversed, so their `time_s` values are 650, then 270, then 40.
   Result: the dropped list is `0:40`, `4:30`, `10:50`.

4. `report/render.py:353`. Class: dead local.
   `title` in `_render_header` is built and never inserted. The document title is the escaped string in `render_html`. `render_html` is the only page builder.

## What I did not check

I did not judge the look, the wording, or the design. I did not open a browser, so I did not click `:target`, switch color scheme, or watch reduced motion. I parsed `/tmp/review-page.html` (94323 bytes, exit 0): 34 ids and no duplicates, and the counts of `section`, `div`, `article`, `details`, `svg`, `ul`, `ol`, `h2`, `h4`, `p`, `a`, `figure`, and `aside` match their closing tags. The fixture page has no `<script`, no `javascript:`, and no `http` URL. The lobby PNG is the base64 payload.

I did not run task 23b, and I did not call the Meta API. `pytest -q` from the worktree: 141 passed in 41.40s.

Map checks that held: route point 0 `(1.31, 6.81)` is `920.0,1515.0`; route point 10 `(-4.1, -10.01)` is `662.2,713.9`; pin f1 `(-4.0, -12.11)` is `translate(667.0 613.9)`; pin f8 `(4.5, -0.1)` is `translate(1072.0 1185.9)`; heat `(3.49, -0.6)` with `r_m` 2.1 is `cx="1023.8" cy="1162.1" r="100.1"`. Corners of the world box land on `(0, 0)` and `(1334, 2048)`. The arrow on route points 3 to 4 is `rotate(-140)`. A synthetic segment to the right is `rotate(0)`, down `rotate(90)`, left `rotate(180)`, up `rotate(-90)`.

These also held. `route.map` values `../../...`, an absolute path, `..`, and `foo/bar` do not load a file outside `report/maps`; a missing map prints one stderr line and omits the map section. Bool is rejected, with the field name, for `summary.lost_s`, `summary.counts.stuck`, `summary.kept`, `at.x`, `resolved_after_s`, a route point, `of`, `here` as `1`, and heat `seconds`. `tests/fixtures/findings_sample.json` and `findings_sample_b.json` load. A missing `summary`, `route`, `cross_player`, or `at` hides that element, including a hand-made file with only one of those blocks. Deleting every `at` leaves the map and no `pin-m` (no nearest-point pin). Fixture cards: learning is one bar and `planned challenge?`, friction `stuck` is two bars, `blocked` is three, both tagged `unplanned`; `abandoned` is `Abandoned`; `solved` with `resolved_after_s` 28 is `Resolved after 0:28`. An unexpected friction or resolved value does not crash. The diff has no em dash, no en dash, no `/Users/` path, and no key-like string.

I did not render `laboratory.json`, and I did not feed the page a corrupt map JSON. I did not screenshot pins on the image.

## Orchestrator response (Claude Sonnet 5.5, Claude Code in T3 Code, 2026-10-28)

All three blocking findings were real and are fixed in the commit after bde28c2; a fresh round 2 follows.

1. `session.id` is now escaped in the h1 (the same class, checked by grep: every other value from the file already went through `_e`). The dead `title` local is removed. `test_every_string_from_the_file_is_escaped` now sets `session.id` too.
2. Times of 0 are real times: one helper (`_first_set`) replaces the `or` chains in `_group_span` and the attempt heading, and a test uses `attempt_start_s` 0.
3. Cards inside an attempt follow `rank`, as the brief says (the design notes' "sorted by time_s" lost). The expected order in `test_groups_and_cards_follow_beat_and_rank` changed to 2, 9, 1, 3, 7, 4, 6, 5, 8. If the analyzer assigns ranks that read badly inside an attempt, that is a ranking question for task 23b, not a page sort.

Nits: dead local removed (4). Left as drawn by the mockup and listed in docs/FOLLOWUPS.md: counts shown from the file's own lists (`3 of 3`, `3 moments`, `(1:25)`), the "level" fallback in the map alt text and title when `session.level` is missing, and the dropped list sorted by time. The analyzer should write these values in 23b so the page copies them.
