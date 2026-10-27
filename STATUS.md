# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Where things stand (2026-10-27, midday)

Sasha's answers of 2026-10-27 are in DECISIONS.md (two entries). Tasks 10 to 17 are done and committed. This repo is on GitHub, private: github.com/Naryadchikov/playtest-lens, `main` pushed.

- **Analyzer (Muse):**
  - `analyzer/client.py`: every API call goes through it, cached and costed, Voice Transcribe included.
  - `spark_test.py` and `transcribe.py`.
  - `findings.py`: the `findings.json` format.
  - `log_candidates.py`:
    - deaths and retries;
    - still stretches split into `idle` (away) and `looking_around`;
    - walk-backs;
    - all mapped to video time through the first flash.
  - `report/render.py`.
  - 52 offline tests pass.
- **Video tools (Grok):** `tools/video.py`: `convert_video`, `extract_audio`, `cut_clip`, `find_start_flash`.
- **Game:** `game/` is at `7ad0f20` on the fork's `playtest-lens`, pushed.
  - The logger: input, scenes, position with yaw and pitch every 0.5 s, and a `user://` log path. Nothing in the log names a person or a machine (task 15's table).
  - The COGITO adapter, now with `death`.
  - The flash and beep at New Game and at each level load.
  - The asset swap, and the door sound trimmed to 0.4 s.
  - docs/PRIOR_WORK.md lists every fork commit.
- No milestone review yet. The first Sonnet review comes after the Spark test's go.

## Next

1. **The Spark test** on Sasha's The Talos Principle 2 recording: a Game Bar mp4 with game sound and his voice, plus `notes.md` in `recordings/spike/`. No event log and no flash. Steps:
   1. Probe it and convert it, and check that one visible moment sits at the same time before and after.
   2. Run a 2-minute stretch where he talks on `muse-spark-1.3` and `muse-spark-1.2`. Show each model's quotes and times next to what he said.
   3. Give the measured cost of the full run, then run it on the model that hears him better.
   4. Make the table against his notes. Go if 7 of the first 10 are real, within about 5 s.
2. Then the quality bar's single-recording lines, and the first Sonnet review (docs/REVIEW.md).
3. **Thursday:** Sasha plays COGITO at `game/` `7ad0f20`, recording before he presses New Game. The idle, walk-back and view-turn numbers are tuned on that log.
4. **Waiting for the go:** the checking pass, the prompts, the cross-player summary, the score.
5. **Waiting for Sasha:**
   - how Game Bar behaves on the PC (DECISIONS.md, 2026-10-27);
   - hearing the door sound in the Lobby.

## Open questions for Sasha

1. **The view-turn number** (Muse's proposal): the view counts as turning when it moves more than 5 degrees between two samples, 0.5 s apart. The orchestrator recommends keeping it with the idle and walk-back numbers until Thursday's log.

Note for the testers' guide (Sasha's words to write): the flash comes when New Game is pressed, so testers start recording before that.

## Credits used

API: $0.00045 of $150 (one Voice Transcribe call, 9 s of audio). Claude: the orchestrator can't read its own usage from inside the harness; check T3 or claude.ai.
