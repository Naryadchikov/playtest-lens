---
name: change-analyzer
description: Change the Playtest Lens analyzer (the pipeline, a prompt, a threshold, the model client) without a second finding path, an uncached model call or tuning on the held-out notes.
---

Use for any change to `analyzer/`.

1. Read PLAN.md, "What we build", and the step you're changing. Trace the current path from the inputs to `findings.json` before editing.
2. Keep one path: candidates, then the check, then the cross-player summary. Change the step in place; never add a second way to make a finding.
3. Every model call goes through the client module: cache by request hash, one line in `runs/costs.jsonl`. Estimate the cost of a new run first; over $10, ask Sasha.
4. A prompt change: edit the file in `analyzer/prompts/`, run it on the tuning sessions only, and keep the before and after findings in `runs/`. Never open the held-out sessions' notes.
5. Add a test with a cached reply in `tests/fixtures/`, so the tests run with no API call.
6. The report page renders `findings.json`; if the page needs a new value, the pipeline writes it.
7. Run the `validate-change` skill.

Report the findings that changed (added, dropped, moved), the cost of the runs, and what you didn't check.

Don't build a framework, a plugin system or a config language for prompts. One function per step is enough.
