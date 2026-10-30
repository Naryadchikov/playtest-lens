# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-28, DECISIONS.md)

Backup mode is on. Claude Sonnet 5.5 hit its limit mid task (access returns 2026-11-01 00:00 UTC). Orchestrator until then: Grok 4.7 through Cursor (docs/BACKUP_ORCHESTRATOR.md). Main author: DeepSeek V4.1 Flash 1017 on Modal. Reviewer of that work: a fresh Grok 4.7. Reviewer of Grok's work: GLM 5.3 (routine) or Kimi K3 (milestones) on Modal. Muse Wonder is not called. The Meta pool (about $23.90) stays for the product's video and audio only. Open-weights mode is Baseten. Sasha's Grok bot and, if needed, his Windows machine stay as before.

Going public is the last step: docs/PUBLIC_CHECKLIST.md.

## Where things stand (2026-10-30, evening)

The pipeline on main is one path. Contributor Spark receives the video with its sound. Open mode is Muse Spark Open on Baseten: the mp4 plus a separate wav, and Voice Transcribe still checks every quote. The frame path is gone. Read DECISIONS.md from 2026-10-29 before changing prompts, the chain, or the editor.

Fork `playtest-lens` is `412e213`: Meeting Room spelling fixed, CEO Office puzzle line is Bear Head. He edits volumes on Windows. The analyzer stays on the Mac.

Player 1's session (git-ignored): `recordings/cogito/cogito_person2.mkv` and `recordings/cogito/2026-10-30T12-20-05Z.jsonl`. Reports in `runs/check/`: `person2-report.html` (Spark, the page to show) and `person2-report-open.html` (Open). The chain versions `person2-report-chain.html` and `person2-report-open-chain.html` stay for reading. The chain code is shelved at `docs/shelved/chain-merge.patch` and is not what `merge_same_moment` does. His own lobby session is still `cogito-report-26.html` and `cogito-report-open.html`.

## In flight

- No analyzer change until he says the Spark page is wrong. Claude polishes the report look when its limit is back. He may reread the Open page and ask Claude to read it too.
- Do not chase the ripped-page combine. Do not build the editor ghost before the submission.
- The repo is still private. The 3-minute video is not recorded. "by design" is still Opus's proposal.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next

1. He finishes reading the Open page if he wants, and Claude reads it when asked. No prompt edits from that unless he says a card is wrong.
2. Claude polishes the report look when the limit is back. Not the findings.
3. He records the 3-minute video from the Spark page: one moment, one drop, the map, then Open beside it. The keypad sentence is his: stuck on the puzzle, not stuck on progression, because of the toilet route.
4. Public checklist, repo public last, submit Wednesday 4 November, well before 9:00 PM Eastern. Freeze Tuesday 3 November.

## Open questions for Sasha

Whether her session may be used to tune prompts, or is kept clean for the score. The word "by design" (Opus's proposal). Nothing else blocks the video.

## Credits used

`runs/costs.jsonl` sums to $18.07 on 2026-10-30. Muse Spark Open on Baseten is $3.94. Voice Transcribe is $0.28. Contributor Spark is $0.17. The Meta pool figure of about $23.90 left was his, on 2026-10-28, and has not been rechecked against Meta's dashboard. Her session's Open check is inside the Baseten figure.
