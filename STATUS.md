# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-28, DECISIONS.md)

Backup mode is on. Claude Sonnet 5.5 hit its limit mid task (access returns 2026-11-01 00:00 UTC). Orchestrator until then: Grok 4.7 through Cursor (docs/BACKUP_ORCHESTRATOR.md). Main author: DeepSeek V4.1 Flash 1017 on Modal. Reviewer of that work: a fresh Grok 4.7. Reviewer of Grok's work: GLM 5.3 (routine) or Kimi K3 (milestones) on Modal. Muse Wonder is not called. The Meta pool (about $23.90) stays for the product's video and audio only. Open-weights mode is Baseten. Sasha's Grok bot and, if needed, his Windows machine stay as before.

Going public is the last step: docs/PUBLIC_CHECKLIST.md.

## Where things stand (2026-10-28, evening)

The pipeline on main is one path: Spark 1.2 windowed candidates, the checking pass, beats, the cross-player summary, the report. Fork `playtest-lens` is `8049b5d`: the level-load fix plus Sasha's Lobby and Laboratory volumes. The first-room video and logs are not here yet. He places volumes and records on Windows (`docs/COGITO_VOLUMES.md`). The analyzer stays on the Mac.

## In flight

- Task 23c is merged: each findings file gets its Across players block. Grok review PASS, no nits (`docs/reviews/10-cross-player-grok.md`). Tests: 147 passed, 1 deselected (`test_extract_audio_from_say_clip`, unrelated, fails inside the sandbox).
- Task 23b is merged: route, heat, pins, markers and the verdict come from the log. Grok review PASS, no nits (`docs/reviews/09-spatial-fields-grok.md`). Tests: 159 passed, 1 deselected. Two notes are in `docs/FOLLOWUPS.md`: a live check still leaves `end_s` empty so `lost_s` is 0, and a pin can fall outside the map picture.
- The verdict template says "1 moment" for one finding and "moments" for more. The author had kept "1 moments" verbatim. The previous orchestrator changed it. Wording and heat thresholds stay proposals.
- Grok bot package 2 is on the fork at `290cba9` (GLM PASS): annotated maps and `tools/volume_report.gd`. Sasha can place volumes from `docs/COGITO_VOLUMES.md`.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next

1. Sasha on Windows: clone `playtest-lens`, place volumes, record with OBS, push the two scenes, copy the video and the log back (`docs/COGITO_VOLUMES.md`).
2. Pull that commit on the Mac, point `game/` at it, run the volume report, then the analyzer.
3. Judgement pass on the first log-zoned report, then tune idle, backtrack and view-turn numbers. The export test can be the same Windows machine after the volumes are saved.

## Open questions for Sasha

Nothing blocking. The verdict sentence and the heat thresholds are proposals. The report look is still his to judge. The open-weights host is decided (Baseten). The checker stays contributor Spark 1.2 for now.

## Credits used

Meta API and Muse Code, one pool: about $23.90 left (Sasha, 2026-10-28). Meta API tracked in runs/costs.jsonl: $13.09 of $150, unchanged this turn (no Meta API call). Modal before these two runs: about $0.02. The Claude harness priced the DeepSeek sessions at $3.86 (23b) and $2.26 (23c) using Anthropic rates, which is not the Modal bill. At DeepSeek's published rates the tokens are about $0.16. Modal billing was not refreshed this turn. Baseten: not used yet.
