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
