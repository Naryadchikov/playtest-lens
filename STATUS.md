# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Where things stand (2026-10-27, late morning)

Sasha's answers of 2026-10-27 are in DECISIONS.md, and tasks 10 to 14 are done and committed.

- **Analyzer (Muse):**
  - `analyzer/client.py`: one module for every API call, with the cache and a cost line per call. It now covers Voice Transcribe too.
  - `analyzer/spark_test.py` and `analyzer/transcribe.py`.
  - `analyzer/findings.py`: the `findings.json` format and its checker.
  - `analyzer/log_candidates.py`: deaths, retries, idle stretches and walk-backs from the event log, mapped to video time through the first flash.
  - `report/render.py`.
  - 46 offline tests pass.
- **One real API call so far:** Voice Transcribe on a 20 s clip of `say` speech. The transcript matched word for word.
- **Video tools (Grok):** `tools/video.py`: `convert_video`, `extract_audio`, `cut_clip`, `find_start_flash`.
- **Game:** `game/` is at `708528e` on the fork's `playtest-lens`, pushed. It has:
  - the logger, the COGITO adapter and the `death` line;
  - the flash and beep at New Game and at each level load (`sync_flash`);
  - the asset swap: a CC0 fire loop, Kenney sliding-door sounds, no flags;
  - five headless tests, all passing.
  docs/PRIOR_WORK.md lists every fork commit.
- No milestone review yet. The first Sonnet review comes after the Spark test's go.

## Next

1. **The Spark test.** It starts when `recordings/spike/` has the recording, `notes.md` and, ideally, the game's log: `~/Library/Application Support/Godot/app_userdata/Cogito/playtest_lens/<time>.jsonl`, from a build at `game/` `708528e`.
   1. Check one scene change in the `.mov` against the converted mp4, and find the flash with `tools/video.py`.
   2. Run a 2-minute stretch where Sasha talks on `muse-spark-1.3` and `muse-spark-1.2`, and show each model's quotes and times next to what he said.
   3. Give the measured cost of the full run, then run it on the model that hears him better.
   4. Make the table against his notes. Go if 7 of the first 10 are real, within about 5 s.
   5. If there's a log, run the log candidates on it too.
2. Then the quality bar's single-recording lines, and the first Sonnet review (docs/REVIEW.md).
3. **Waiting for the go:** the checking pass, the prompts, the cross-player summary, the score.
4. **Waiting for Sasha:** his check of how Game Bar behaves on the PC (DECISIONS.md, 2026-10-27, answer 3).

## Open questions for Sasha

1. **The log candidates' numbers.** Muse's proposal, in `analyzer/log_candidates.py`:
   - idle: 10 s with no input and under 0.5 m of movement;
   - backtrack: back within 2 m of a point passed 5 s or more earlier, after getting 5 m or more away from it.
   The orchestrator recommends keeping them until a real log shows how often they fire, then tuning on that log. Looking around isn't logged as input, so 10 s may flag reading or looking.
2. **The sliding door's open sound** (Grok's pick): Kenney's `stoneDrag4`, 1.7 s long, while the door slides in 0.3 s. Listen in the Lobby and say if it's fine.
3. **Worktrees as a standing rule.** The orchestrator proposes removing each author's worktree once its work is committed, without asking each time. Two are on disk now, Muse's tasks 11 and 13, and both are committed.

Note for the testers' guide (Sasha's words to write): the flash comes when New Game is pressed, so testers start recording before that.

## Credits used

API: $0.00045 of $150 (one Voice Transcribe call, 9 s of audio). Claude: the orchestrator can't read its own usage from inside the harness; check T3 or claude.ai.
