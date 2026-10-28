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

