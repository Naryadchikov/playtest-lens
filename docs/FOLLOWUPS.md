# Follow-ups

One list for things found but not fixed: a pre-existing review finding, a case that could happen but hasn't, an idea that would widen the scope. One line each, with where it came from. Swept before the freeze.

- The COGITO adapter logs a pickup only when the item lands in a new inventory slot (`picked_up_new_inventory_item`). A pickup that stacks onto an existing slot, and currency with `add_on_pickup`, write no line. From task 07 (Grok's report), 2026-10-27.
- Cached input tokens are billed at the full input rate in analyzer/client.py compute_cost; the cached rate ($0.15 per million) is ignored, so a mostly cached reply logs too high a cost. From the Grok re-review of tasks 01 and 11, 2026-10-27.
- tools/video.py cut_clip partly succeeds on a centre outside the recording (it clamps) instead of failing; only a fully outside window raises. From the Muse re-review of task 09, 2026-10-27.
- Headless sync_flash stamps are about one frame late and mark a flash never drawn; windowed stamps are correct. Analyzer docs say headless stamps are approximate (analyzer/log_candidates.py). From the Muse re-review of tasks 06 to 15, 2026-10-27.
- The COGITO adapter _inventories guard is never cleaned up, unlike _watched; a long session keeps dead instance ids. From the Muse re-review of tasks 06 to 15, 2026-10-27.
- test_sync_flash.gd finds the flash by polling the log file, so a slow machine could fail it on timing, not logic. From the Muse re-review of tasks 06 to 15, 2026-10-27.
- analyzer/client.py upload index never expires a file id the server has dropped, so a stale id is reused forever. From the Grok re-review of tasks 01 and 11, 2026-10-27.
- analyzer/transcribe.py lets an HTTP error out as a traceback where spark_test.py prints a clean message and returns 1. From the Grok re-review of tasks 01 and 11, 2026-10-27.
- The Pixabay entries in docs/PRIOR_WORK.md rest on the license summary, not the full binding text, and the credits page swaps two authors. No attribution is required. From the Muse re-review of tasks 05 and 14, 2026-10-27.
- merge_candidates raises KeyError on an unknown future log kind instead of a clean message, before any model call. From the Grok review of the log merge, 2026-10-27.
- The telemetry test's `marker` lines carry an extra `where` field while docs/LOG_SCHEMA.md says `marker` has no fields: align the doc or the test. The first `perf` line reads fps 1.0 because Godot's counter is not warm: skip or flag it. From Sasha's Grok bot retest of the logger, 2026-10-28.
- Beats grouping limits, all non-blocking: a dropped unsolved moment updates an area's recency (`analyzer/beats.py`, `assign_beats`); overlapping zones resolve to the earliest start and an unclosed zone matches every later time; after a gap over 180 s an attempt's end stays on its first moment; a later unzoned "East Lab Wing" folds into a zone named "East Lab"; rooms that share one word ("North Hall", "South Hall") keep an identical generic label as Attempt 2 of the older room; within 300 s an identical fan, hexahedron, jammer or keypad label fuzzy-joins across rooms with no shared words. If a COGITO run shows these, replace the fuzzy matching with checker-chosen ids. From Grok review round 7, 2026-10-28.


## Open-weights backend (task 21 review, Grok, 2026-10-28)

- The frame helpers (`sample_frames`, `_frame_plan`) were deleted in task 27 (2026-10-29). The open path sends video plus a wav. The three frame bullets below are closed with that deletion.
- Tests do not cover a marker in the middle of an open reply.

## Open path, video plus wav (task 27 review nits, Opus, 2026-10-29)

- ffmpeg writes its version into the wav header, and that wav's hash is part of the open-model cache key. An ffmpeg upgrade misses every cached open reply and bills Baseten again. `-bitexact` on `extract_audio`, or keying on the video hash alone, would stop that. Same machine and same ffmpeg are fine until then.
- `_call_open_model` extracts the wav before the cache lookup, so a cached rerun still runs ffmpeg once per call.
- A finding merged away still leaves its 20 s clip under `runs/`. The files are git-ignored.

## Spatial fields (task 23b, 2026-10-28)

- The report draws one map per report: task 23b picks the scene with the most time with position samples, and positions in every other scene are ignored for the route, the pins and the F9 markers. A session that visits two mapped levels loses one of them, and an unmapped scene that holds the most time hides the map section even when another scene has a map. From task 23b (DeepSeek V4.1 Flash), 2026-10-28.
- A live check still writes every finding with `end_s` null (`analyzer/check.py`, pre-existing, outside the 23b diff). `lost_s` is then 0, because the spatial module only sums spans that have an `end_s`. The fixture files already carry `end_s`. Grok review note, 2026-10-28.
- A pin can sit outside the map picture when the logged position is outside the map's world box. On the lobby fixture the map ends at world x 10 and one sample is at x 17.86. Grok review note, 2026-10-28.
- The lobby plan is one flat slice. It draws every object's x and z and ignores height, so the CEO office (upper floor, the laptop) sits on the ground plan. Volumes already separate floors by height. Next round: a second slice, or draw only the floor the player is on, once the lobby report shows the stacked route. Sasha, Cursor chat, 2026-10-28, with the annotated lobby map.

## Report page redesign (task 23 review nits, 2026-10-28)

- The page still derives a few labels from the file's own lists: "N of M" in Across players (`len(players)`), "N moments" on a player chip and in a puzzle note, the span `(1:25)` on a card (`end_s - time_s`), the dropped count and the dropped list order (sorted by time). When the analyzer writes these in task 23b (`cross_player` counts, per-finding span, dropped order), make the page copy them.
- Without `session.level`, the map's alt text and title say "the level". Hide or reword when the level is missing.

## Lobby report fixes (task 25, 2026-10-28)

- Neighbouring sections with one area name (two "CEO Office" sections at 3:18 and 3:52) could merge on the page. Left as two. From task 25, 2026-10-28.
- A "recent trail only" option on the map timeline (show only the last N seconds of route) if the growing route still overlaps. Sasha's call on N. From task 25, 2026-10-28.
- Unzoned moments in a zoned session still take the checker's free area wording ("Central Office - Meeting Room Hunt", "Office Complex"), and the fuzzy matching can file a later moment under an older wording (rank 20 at 8:22, the crash, lands in the paper hunt). From task 25, 2026-10-28.

## Visit merge (task 28, GLM review, 2026-10-29)

- The 8-second chain for findings with no zone is not reset by a room visit in between. Two corridor stucks 8 seconds apart can fold together even when a room visit sits between them. Less folding than the old rule. From docs/reviews/17-system-glm.md.

## Report page (review 18, Grok, 2026-10-31)

- Print does not hide the clip: `@media print { .clip { display: none } }` loses to `.clip.video { display: block }` on specificity, so a printed page keeps the video box. Pre-existing; the task 29 redesign rewrites this CSS. From docs/reviews/18-report-polish-grok.md.
