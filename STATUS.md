# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-28, DECISIONS.md)

Backup mode is on. Claude Sonnet 5.5 hit its limit mid task (access returns 2026-11-01 00:00 UTC). Orchestrator until then: Grok 4.7 through Cursor (docs/BACKUP_ORCHESTRATOR.md). Main author: DeepSeek V4.1 Flash 1017 on Modal. Reviewer of that work: a fresh Grok 4.7. Reviewer of Grok's work: GLM 5.3 (routine) or Kimi K3 (milestones) on Modal. Muse Wonder is not called. The Meta pool (about $23.90) stays for the product's video and audio only. Open-weights mode is Baseten. Sasha's Grok bot and, if needed, his Windows machine stay as before.

Going public is the last step: docs/PUBLIC_CHECKLIST.md.

## Where things stand (2026-10-29, morning)

The pipeline on main is one path. Contributor Spark receives the video with its sound. Open mode is Muse Spark Open on Baseten: the mp4 plus a separate wav, and Voice Transcribe still checks every quote. The frame path is gone. Opus review of that change: PASS, no blocking findings (`docs/reviews/16-fixes-now-opus.md`). Tests: 184 passed, 1 deselected (the say-clip test, sandbox). He reruns the session himself after he updates the volumes.

Fork `playtest-lens` is `8049b5d`: the level-load fix plus his Lobby and Laboratory volumes. The doc's expected hash `290cba9` is stale. He edits on Windows (`docs/COGITO_VOLUMES.md`). The analyzer stays on the Mac. The lobby recording and four logs are in `recordings/cogito/` (git-ignored). Reports from that session, also git-ignored: `runs/check/cogito-report-26.html` (contributor), `cogito-report-open.html` (frames plus transcript), `cogito-report-modal-video.html` (dropped), `cogito-report-baseten-av.html` (video plus wav, outside the client).

## In flight

- Task 27 is implemented and reviewed, not yet his rerun. Same-kind cards within 8 seconds merge. The time-lost tile hides when `lost_s` is 0, because the check still writes `end_s` null. The tag "by design" is Opus's proposal.
- The verdict template and the heat thresholds stay proposals.
- A submission is not ready: the repo is private, the README has run steps but no video, and there is no second player. Overview: `docs/reviews/15-state-overview-opus.md`.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next

1. Sasha on Windows: pull `playtest-lens` (tip `8049b5d` before his edits), fix the volumes, commit only the two scene files, push, and copy the new video and log to the Mac.
2. He looks at two cards on `cogito-report-baseten-av.html`: the Cutscene Trigger label at 1:53, and the hidden-room sculpture called a lion head. The word "by design" is his to change.
3. After the new log is here, rerun contributor and the locked open path. Then a second player, blind notes, the 3-minute video, and the public checklist.

## Open questions for Sasha

The word that replaced "planned challenge?" ("by design", Opus's proposal). Whether a second player is available this week. Nothing else blocks his volume pass.

## Credits used

`runs/costs.jsonl` sums to $15.72. Of that, Muse Spark Open on Baseten is $1.85, including this morning's video-plus-wav session at $0.57. Voice Transcribe is $0.12. Contributor Spark is $0.07. A Modal video report of about $0.50 was billed to his Modal balance and is not in that file. The Meta pool figure of about $23.90 left was his, on 2026-10-28. No new Meta call was made for the video-plus-wav experiment.
