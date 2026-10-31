# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-31, DECISIONS.md)

Backup mode is over. Claude Opus 5.5 orchestrates and writes the code. A fresh Grok 4.7 xhigh through Cursor reviews the code; a fresh Claude Sonnet 5.5 judges the report captures and the README. Muse Wonder is not called. The Meta pool stays for the product's video and audio only. Normal mode is Contributor Spark 1.2; open mode is Muse Spark Open on Baseten. The table is in AGENTS.md.

Going public is the last step: docs/PUBLIC_CHECKLIST.md.

## Where things stand (2026-10-31, evening)

Main has the model setup (`c10fbc2`) and the report polish (`b36e564`). The polish is look only: each clip sits beside its card text on wide screens, the map fits one screen with its controls, zero tiles step back, lighter route arrows, the start label clear of pin 1, and one time instead of "0:39-0:39". Both person2 pages are regenerated from the same findings files; their visible text differs only in those single-time spans. The old pages are kept as `runs/check/person2-report-before-polish.html` and `person2-report-open-before-polish.html`.

The pipeline is unchanged: one path, Contributor Spark with sound, Open on Baseten with the mp4 plus a wav and Voice Transcribe checking quotes. Fork `playtest-lens` is `412e213`. The chain stays shelved (`docs/shelved/chain-merge.patch`).

Player 1's session (git-ignored): `recordings/cogito/cogito_person2.mkv` and `recordings/cogito/2026-10-30T12-20-05Z.jsonl`. The page to show is `runs/check/person2-report.html` (Spark); Open is `runs/check/person2-report-open.html`.

## In flight

- Task 30 (Opus subagent): the redesigned report, mockup B as base (two floors, sticky map that follows the moment, session strip, Play, problems block). Brief: docs/tasks/30-report-build.md. Then Grok reviews the code, Sonnet the captures.
- Task 31 (Opus subagent): the add-on as a real Godot plugin, fork only. Brief: docs/tasks/31-addon-plugin.md. Then Grok reviews.
- Fork `playtest-lens` has `1bd0281` (map export per floor), local, not pushed until reviewed with task 30. Main has both floor maps (`1cb117f`).
- Sasha marks the 24 Spark cards on `runs/check/person2-marking.html` (git-ignored) and pastes the picks.
- Her consent for the public video: he is asking her. Nothing of hers goes public before her yes.
- No analyzer prompt change until he says a card is wrong. No third blended report, no editor ghost, no ripped pages.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next

1. He looks at the polished Spark page. Look notes go to Opus; the look is his call.
2. He records the 3-minute video from the Spark page: one moment, one drop, the map, then Open beside it. The keypad line is his.
3. Freeze Tuesday 3 November: a fresh Grok 4.7 on the whole repo and a fresh Sonnet 5.5 on the README and page captures (docs/REVIEW.md).
4. Public checklist (docs/PUBLIC_CHECKLIST.md), repo public last, submit Wednesday 4 November, well before 9:00 PM Eastern.

## Open questions for Sasha

1. Is her session for tuning, or kept clean for the score? Nothing is tuned until he answers.
2. The word "by design" (Opus's proposal).

## Credits used

`runs/costs.jsonl` sums to $18.07 on 2026-10-31 (no model calls today). Muse Spark Open on Baseten is $3.94. Voice Transcribe is $0.28. Contributor Spark is $0.17. The Meta pool figure of about $23.90 left was his, on 2026-10-28, and has not been rechecked against Meta's dashboard. Her session's Open check is inside the Baseten figure.
