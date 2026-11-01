Reviewer: Grok 4.7 (xhigh), Cursor via T3. Commits cece6b7 and 9e4e748 (Claude Opus 5.5).

**PASS.**

Findings: none.

## What held

### Log slices stay on the raw intervals

`_merge_reentries` runs only from `assign_beats` (`analyzer/beats.py:383`). `zone_intervals` is unchanged from f397f7e, and `log_slice_text` still reads it (`analyzer/check.py:176`). `assign_beats` copies the zone dicts: the list it is given is unchanged after the call.

Clip windows are the checker's: `time_s` minus 10 seconds, plus 10 seconds, clamped to the candidates file's `duration_s`, then rounded to 2 decimals the way `clamp_time` does. Every window matched the stored `clip.start_s` and `clip.end_s` of the finding with that `time_s` (0 mismatches).

Compared `/tmp/r32-base` at f397f7e with this tree, for every candidate. Her log is `recordings/cogito/2026-10-30T12-20-05Z.jsonl` at flash 15.568. His log is `recordings/cogito/2026-10-28T20-31-08Z.jsonl` at flash 25.2. Zone lists and slice bytes match at both commits:

| Session | Candidates | Slice bytes |
|---|---:|---:|
| Her Spark | 32 | 711688 |
| Her Open | 55 | 1256882 |
| His Spark | 16 | 287695 |
| His Open | 18 | 314392 |

`check._place` is not in this diff. It still requires a strict contain, so a moment just outside a volume is not folded into another card. Non-beat fields are unchanged, below.

### Grouping

`_zone_at` (`analyzer/beats.py:50`): a volume that contains the time wins over one that is only nearby, and among volumes that contain the time a puzzle line wins. Otherwise the nearest edge within 5.0 seconds wins, including a gap of exactly 5.0. A gap of 5.01 does not.

Probes, video flash 101:

- Room 110 to 150 and Bear Head 115 to 140, moment at 120: puzzle Bear Head, one attempt.
- Bear Head 120 to 130 and 132 to 150, room open 110 to 180. Moments at 125 and 140 are Bear Head, attempt 1, span 120 to 150. The moment at 131 is in the 2 second gap and inside the room. The merged span covers 131, so it is the same Bear Head attempt. That is the one-visit rule: the step out is part of the visit. No kept moment in the four files picks a different zone from the raw intervals than from the merged ones.
- Equal gaps of 5.0: the later interval in start order wins. Puzzle then room assigns the room. Room then puzzle assigns the puzzle. No kept moment in these files is within 0.05 seconds of two edges.
- An open interval (`end_s` None) does not raise. A time inside that room and inside a puzzle returns the puzzle. A time 5 seconds before the open room joins the room when nothing else contains it. These two logs have no unclosed volume.
- A re-entry gap of exactly 5.0 seconds is one attempt. A later gap of 15 seconds is the next attempt.

Every merged gap in the two logs is at most 5 seconds: her Code Lock 0.17 seconds at 860.59, his Code Lock 0.76 seconds at 360.0 and 1.81 seconds at 484.13, plus lobby, CEO Office, Bear Head, and Archive Toilet gaps from 0.06 to 4.46 seconds. Her lobby gap of 5.4 seconds (118.65 to 124.05) stays two visits.

Her Spark f22 at 842.0 seconds is 0.47 seconds before Archive / Code Lock at 842.47, inside no other volume. Puzzle goes from null to Code Lock, attempt 2, span 842.47 to 887.21, the same span as f23 once the 0.17 second step out is one visit.

His Spark f12 at 339.0 seconds is 0.78 seconds before Code Lock at 339.78, inside no other volume. Puzzle goes from null to Code Lock, attempt 1, span 339.78 to 361.93, which includes the 0.76 second step out.

Those are the only puzzle-field changes. Her Open has no finding within 2 seconds of 842. His Open f12 is at 341 seconds and was already Code Lock; the span end moves from 360.0 to 361.93.

The other beat edits are spans, indexes, and zone fills from the same rules. Her Open f23 at 571 seconds is 3.38 seconds before CEO Office at 574.38, so the area becomes CEO Office instead of the checker's UPPER_OFFICE_CEO. The puzzle stays null.

`assign_beats` on the before-edge cards matches the current beats in all four files (0 mismatches). `assign_beats` is the only writer of `beat`.

### Time-stuck spans

`zones` on the four files is identical to `runs/final/before-edge/`. The page's room bar is still the raw intervals. `spatial.enrich` stores `zone_intervals` (`analyzer/spatial.py:674`), not the merged visits.

`_lost_s` still uses `beat.attempt_start_s` to `attempt_end_s` (`analyzer/spatial.py:462`). A fresh `_summary` of the regrouped cards matches the stored summary on all four files (0 diffs). Each stuck span that changed equals that merged zone:

- Her Spark f22: no span, then 842.47 to 887.21. f23: 860.76 to 887.21, then 842.47 to 887.21. f27: start 1038.56, then 1024.44 (lobby gap 2.92 seconds).
- Her Open f34: the same Code Lock join as f23.
- His Spark f12: no span, then 339.78 to 361.93.
- His Open f8, f10, f11, and f12: each new span is that merged zone.

Her Spark `lost_s` goes from 342.49 to 374.90. The 32.41 seconds are the Code Lock problem (64.11 to 82.40, the 18.29 seconds from 842.47 to 860.76) and Lobby (113.30 to 127.42, f27's earlier start). The Archive problem that held only f22 is gone. f22 sits on Archive, Code Lock with f4, f23, and f28.

His Spark `lost_s` goes from 0 to 22.15, which is 361.93 minus 339.78. The Archive problem (f3, f6, f12) becomes Archive, Code Lock with f12 only. f3 and f6 are learning, so they leave the problems block with the stuck moment.

### Only beats and summary differ

Against `runs/final/before-edge/`, `events`, `format`, `markers`, `route`, `session`, and `zones` have 0 diffs. On each finding, every field except `beat` has 0 diffs. `cross_player` is absent in both copies. Summary diffs are `lost_s` and `problems` only.

Nothing from `runs/` or `recordings/` was copied into a tracked file. The diff of these commits under `analyzer/`, `report/`, and `tests/` is the four source files (126 insertions, 19 deletions). No key, token, or em dash.

### Page words

`_name` (`report/render.py:679`) turns `CUBICLE_AREA` into `Cubicle area`, `Archive, BREAK_ROOM` into `Archive, Break room`, and `COGITO_3_Lobby` into `COGITO 3 Lobby`, and leaves `Break Room`. It is used for the moment place (`_place`), the group title, problem places, across-player places, and the room bar's text, title, and `data-room` (`report/render.py:1335`).

The script still takes the room from `dataset.room` (`report/render.py:1461`, `roomAt` at 1526). For every finding in the four files, `_place` and `_group_title` contain no raw `WORD_WORD` token. Rendered headers, problem lists, and room bars for both of his pages and her Spark page are the same, except the h1 id in `Playtest cogito_person2`, which is the session id in `Playtest {id}`.

Model tag, from `LABELS["head"]["model_names"]`: Spark pages render `Analyzed by <b>Muse Spark 1.2</b>` with `title="muse-spark-1.2-contributor"`. Open pages render `Muse Spark Open (open weights)` with `title="meta-models/muse-spark-open-1026"`. A probe id `evil<model>` is escaped in the tag and in the title attribute (`evil&lt;model&gt;`). The h1 escapes the id and the player. Room text, the room title, and `data-room` escape quotes and `<`.

The h1 is `Playtest {id}` (`LABELS["session"]`). The document `<title>` still uses `LABELS["title"]` (`Playtest Lens: session {id}`), which this diff does not change.

### Tests

`.venv/bin/python -m pytest -q`: 249 passed, exit 0, 40.76 s. `runs/costs.jsonl` stayed 1361 lines. The cost fields that are present sum to $29.61. No model call from this review.

On f397f7e the three new beat tests raise AssertionError. `test_raw_volume_names_read_as_words` raises AttributeError because `_name` is absent. The old header is `Analyzed with <span class="mono">muse-spark-1.2-contributor</span>.`, and `LABELS["head"]` has no `model_names`, so the updated model-line test fails there too.

## What I did not check

I did not open the page in a browser, play a clip, or judge the wording or the look. I did not read held-out notes or the Keychain, and I did not call a model. I did not review `godot/`, `game/`, or the commits in this range outside `analyzer/`, `report/`, and `tests/` (the rules, the decisions, the tester guide). I did not re-audit the pre-existing attempt end for a volume that never closes: these logs have none, and that branch of `assign_beats` is not in this diff.
