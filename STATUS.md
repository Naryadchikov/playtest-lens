# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-28, DECISIONS.md)

Orchestrator: Claude Sonnet 5.5 (Claude Code, about $10 of usage; more Claude returns Saturday evening 2026-10-31). Main author: DeepSeek V4.1 Flash 1017 on Modal through `tools/run-modal-agent.sh`. Second author and every reviewer: Grok 4.7 xhigh through Cursor. Muse Wonder is not called, and the Meta pool (about $23.90) is kept for the product's video and audio processing only. The open-weights mode is separate, so Sasha can enter several hackathon categories. His Windows machine may join later. Sasha's Grok bot (own VM) takes parallel Godot work. Modal endpoint `deepseek-1017` is live and smoke-tested (a Read tool call through the wrapper worked).

Backup plan if Claude's usage runs out before Saturday: docs/BACKUP_ORCHESTRATOR.md. Going public is the last step: docs/PUBLIC_CHECKLIST.md.

## Where things stand (2026-10-28)

The pipeline is one path: Spark 1.2 windowed candidates, the checking pass, beats (Area, Puzzle, Attempt, Sub-beat), the cross-player summary, the report. Telemetry volumes, a schema 1 log with pause and perf lines, and the COGITO fork are in place. Committed and pushed 2026-10-28: the beats work and the logger schema (fork `playtest-lens` at `dc8c771`, main `3a090ad` plus the docs commit). Grok's beats review ran 7 rounds; round 7 is PASS (docs/reviews/06-area-beats-grok.md). 102 tests pass, Talos recompute 0 mismatches. The non-blocking grouping limits are in docs/FOLLOWUPS.md: if a COGITO run shows them, replace the fuzzy matching with checker-chosen ids.

## In flight (2026-10-28, evening)

- Done and pushed: Baseten open-weights backend (task 21, Grok PASS), the Grok bot's Godot work (task 22, GLM PASS; fork `playtest-lens` at `b0a52cf`), contributor Spark as the default, tester guide log path.
- Done: report page redesign (task 23), merged e33c046 after Grok review round 2 PASS. Fictional fixture page: `runs/redesign/page.html` (git-ignored). Nobody has looked at it in a browser yet: Sasha judges the look. Task 23b (the analyzer computes route, heat, pins, summary, cross-player from the log) is next and needs Sasha's yes.
- Grok bot, package 2 (docs/tasks/24-grok-bot-2.md): scene inventory and volume report, pasted by Sasha, in progress on the bot's VM.
- Sasha, in a few hours: telemetry volumes in COGITO (docs/COGITO_VOLUMES.md), then the Mac play session with recording (steps in the same file), then the Windows build test with OBS.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next

1. Sasha plays COGITO with telemetry volumes, recording before New Game.
2. Judgement pass on the first log-zoned report, then tune idle, backtrack and view-turn numbers.
3. Open-weights mode (Spark Open, Baseten key in the Keychain, or Modal's Shared Endpoint for Muse Spark Open).

## Open questions for Sasha

Answered: the Muse balance and the $150 API credits are one pool, about $23.90 (so every Wonder check draws on it), and Modal credits do pay for Shared Endpoint tokens. Open: the open-weights host and the checker model, in the plan sent to Sasha.

## Credits used

Meta API and Muse Code, one pool: about $23.90 left (Sasha, 2026-10-28). Meta API tracked in runs/costs.jsonl: $13.09 of $150 (Spark passes, three Talos checking runs, transcripts), at 2026-10-28. Modal: about $0.02, paid from credits (billing summary shows Credits -0.02, Billed $0.00). Baseten: not used yet.
