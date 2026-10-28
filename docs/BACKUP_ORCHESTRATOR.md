# Backup orchestrator

For the case where Claude's usage runs out before Saturday evening (2026-10-31), when Sasha's Claude Max limits reset. A proposal from the Claude Sonnet 5.5 orchestrator (Claude Code in T3 Code), 2026-10-28, shaped by Sasha's ideas. It becomes the plan only when Sasha starts a thread on it. Until then Claude orchestrates and this file just waits.

## How to switch

1. Sasha opens a new thread in T3 Code on the `cursor` provider, model Grok 4.7 (reasoning xhigh, fast mode on), in this repo on `main`.
2. First message: "Read docs/BACKUP_ORCHESTRATOR.md, then STATUS.md, DECISIONS.md and AGENTS.md, then continue."
3. The outgoing orchestrator brings STATUS.md up to date before it stops (what is running, which round a review is on, what is uncommitted, what Sasha owes an answer on).

## Who does what in backup mode

| Role | Who | Notes |
|---|---|---|
| Orchestrator | Grok 4.7 xhigh through Cursor | Plans, briefs, follows runs, reads verdicts, keeps STATUS.md and DECISIONS.md, fixes about 20 lines or less. Does not author features |
| Main author, analyzer and report | DeepSeek V4.1 Flash 1017 on Modal | `tools/run-modal-agent.sh deepseek "<brief>"` from inside the author's worktree |
| Godot and tools | Grok through Cursor, or Sasha's Grok bot on its VM | Grok works directly in `game/` on `playtest-lens` for Godot tasks (AGENTS.md) |
| Reviewer of DeepSeek's work | A fresh Grok 4.7 xhigh thread each round, started by `delegate_task` on the `cursor` provider | Different vendor from the author |
| Reviewer of Grok's work, routine | GLM 5.3 on Modal: `tools/run-modal-agent.sh glm "<brief>"` | Different vendor from both Grok and DeepSeek; $1.40 in, $4.40 out per million tokens |
| Reviewer of Grok's work, milestones and the freeze | Kimi K3 on Modal: `tools/run-modal-agent.sh kimi "<brief>"` | Stronger and dearer: $3 in, $15 out per million |
| Meta pool (about $23.90) | The product's video and audio processing only | Spark candidates, Voice Transcribe. No agent work bills to it. Muse Wonder is not called |
| Open-weights mode | Its own track (Baseten or Modal, Spark Open) | Billed separately from the Meta pool |
| Sasha's Windows machine | Optional | May join the process later if needed |

The orchestrator and the reviewers never edit the files under review. A reviewer's brief says "Do not call any t3-code tools" and "never run rm".

## Why these picks

- **Grok orchestrates:** the strongest judgement outside Claude that Sasha has, Cursor is close to unlimited, and T3 lets a `cursor` thread start child tasks. Untested as an orchestrator: the first thing the new orchestrator does is one small `delegate_task` call to confirm.
- **Kimi K3 or GLM 5.3 for Grok's work:** a third vendor beats DeepSeek reviewing it, and Modal's credits ($130 on 2026-10-28, not touched by agent work so far) cover them. Kimi is the better reviewer and costs about $1 a round; GLM costs a third of that.
- **DeepSeek as orchestrator was rejected:** it writes the code, and the orchestrator briefs the reviewers of that code.

## Rules that stay

Everything in AGENTS.md and DECISIONS.md: no key or tester media in the public repo, keys only in the Keychain (`MODAL_PROXY_TOKEN`, `BASETEN_API_KEY`, `META_API_KEY`, each read for one process only), Sasha decides design, every "decided" needs his quote, no em dashes, English everywhere, small commits on `main`, push only `main`, and the fork's `playtest-lens` branch for Godot. Ask Sasha before any run you expect to cost more than $10 of Modal credits.

## Smoke-test status of the Modal models (2026-10-28)

All three endpoints are live and each passed the same test: `tools/run-modal-agent.sh <name> "Read a.txt and reply with its content" --allowedTools Read` returned the file's text, so tool calling works through the Claude Code harness. Endpoints: `deepseek-1017` (`deepseek-ai/DeepSeek-V4.1-Flash-1017`), `glm-53` (`zai-org/GLM-5.3`), `kimi-k3` (`moonshotai/Kimi-K3`). Not tested: a real review by GLM or Kimi, and Grok as an orchestrator.
