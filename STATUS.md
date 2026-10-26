# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Where things stand (2026-10-26, evening)

- **Tools:** git, gh (logged in), Python 3.13 (`.venv` with `openai`, `pytest`), ffmpeg 9.0.2, Godot 4.7.2 at `/Applications/Godot.app` (not on PATH), its export templates (SHA512 checked against the release), muse 1.4.13, cursor-agent.
- **Authors:** Muse on Wonder and Grok 4.7 both work as T3 subagents; both report `META_API_KEY` missing in their environment.
- **Repo:** local `main` only, not pushed. The first commit was rewritten without the zip (decision 7).
- **Key:** in the Keychain; `tools/run-analyzer.sh` gives it to the analyzer's process only.
- **Task 01 (Muse):** `analyzer/client.py` (cache, cost line) and `analyzer/spark_test.py` (`--model`, `--start`, `--seconds`). 9 offline tests pass. No real API call yet, so the live reply shape is untested.
- **Sasha's answers to questions 1 to 9** are in DECISIONS.md.

## Next

1. The Spark test (decision 9): when `recordings/spike/` has the recording and `notes.md`, find a 2-minute stretch where Sasha talks and run it on `muse-spark-1.3` and `muse-spark-1.2`. Show each model's quotes and times next to what he said. Then give the measured cost of the full run, run it on the model that hears him better, and make the table of flagged moments against his notes. Go if 7 of the first 10 are real, within about 5 s.
2. Check the quality bar's single-recording lines (right times, real input, offline tests), with evidence.
3. If Sasha says go: the first Sonnet review of the client (docs/REVIEW.md), then PLAN.md's Wed tasks.

## Open questions for Sasha

None. Waiting for the recording and its notes.

## Credits used

API: $0 of $150 (no real call yet). Claude: the orchestrator can't read its own usage from inside the harness; check T3 or claude.ai.
