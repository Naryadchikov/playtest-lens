Reviewer: Grok 4.7 (xhigh, fast) through Cursor in T3 Code. Commit 9f323e0.

PASS

## Blocking

None.

## Nits

None.

## What I did not check

I did not judge the look, the wording, or the design. I did not open a browser, so I did not click `:target`, switch color scheme, or watch reduced motion. I did not run task 23b, and I did not call the Meta API. I did not re-measure arrow angles or the world-box corners. I did not render `laboratory.json`, and I did not feed the page a corrupt map JSON.

Re-checked on this commit, and they held.

1. `report/render.py:353` escapes `session.id` before the h1 at line 376. The title at line 971 escapes the whole title string. Input `</h1><img src=x onerror=alert(1)>` stays inside the one h1, as text. Input `<script>alert(1)</script>` is escaped in the h1 and the title. The same script string, and the attribute breakout `"><script>alert(1)</script>`, placed in the session strings, the verdict, place, kind, player label, summary, quote, game state, check note, friction, resolved, beat area, puzzle, zone, and clip path, leaves the page with one `<img` (the map picture) and no `<script`.

2. `report/render.py:833` `_first_set` keeps the first value that is not None. It is what `_moment_end` (line 838), `_group_span` (lines 843 and 847), and the attempt heading (lines 887 and 890) use. Input A, the first kept finding with `attempt_start_s` 0, `attempt_end_s` 90, `time_s` 12, `end_s` 20, and the other findings removed: heading `Attempt 2 (0:00-1:30)`, note `1 attempt, 1 moment, 0:00-1:30`. Input B, `attempt_start_s` 5, `attempt_end_s` 0, `time_s` 5, `end_s` 40: heading and note `0:05-0:00`. The card's own span is `0:05-0:40`. Input C, attempt 1, `attempt_start_s` 10, `attempt_end_s` null, `time_s` 15, `end_s` 0: heading and note `0:10-0:00`, card `0:15-0:00`. Also shown as zero: `worst_t` 0 renders `P0: 0:00`, `resolved_after_s` 0 renders `Resolved after 0:00`, heat `seconds` 0 renders `0:00` with `r="0.0"`, marker `t` 0 renders `F9 marker at 0:00`, `lost_s` 0 renders `0:00` on the time-lost tile, attempt number 0 renders `Attempt 0`, and `puzzle_number` 0 renders `Puzzle 0`. World `(0, 0)` is drawn at `857.6, 1190.7`. An attempt whose start is 0 sorts before a start of 10. The other `or` expressions in `report/render.py` are strings, empty containers, or an explicit None check (`resolved` at line 666). `analyzer/findings.py` has no numeric `or` fallback; a time of 0 loads, and a null or bool `time_s` raises ValueError naming `time_s`. `_first_set(None, None)` raises StopIteration. Every call site also passes `time_s` or a value taken from it, and the loader requires `time_s` to be a number, so a loaded file cannot reach that raise. A loaded file with `end_s`, `attempt_start_s`, and `attempt_end_s` all null and `time_s` 0 renders `0:00`.

3. `report/render.py:885` sorts cards by `rank`. Fixture card ids are `2, 9, 1, 3, 7, 4, 6, 5, 8`. North attempt 1 is rank 9 at 192s and rank 2 at 200s, and the page shows 2 then 9. South attempt 1 is rank 6 at 670s and rank 4 at 740s, and the page shows 4 then 6. Reversing the findings array leaves that order. Reversing route points, markers, heat spots, and `cross_player` entries changes the page to the new file order. Kept findings are sorted by rank at line 934. The dropped list is still sorted by `time_s` at line 938. That nit, the derived labels, and the missing-level fallback stay in `docs/FOLLOWUPS.md` and do not block.

`pytest -q` from the worktree: 142 passed in 40.62s. The three fixture pages have an empty tag stack and no duplicate ids (redesign 34 ids, 94323 bytes; sample 5 ids, 13631 bytes; sample_b 3 ids, 11892 bytes). Counts of `section`, `div`, `article`, `details`, `svg`, `ul`, `ol`, `h1`, `h2`, `h3`, `h4`, `p`, `a`, `figure`, `aside`, `li`, and `video` match their closing tags. `img` and `meta` are void. No `<script`, no `javascript:`, and no `http` URL. The diff has no em dash, no en dash, and no key. It has no home directory. The round 1 report added in this commit names a temp html file and quotes a home-directory prefix in the sentence that records that prefix was absent.
