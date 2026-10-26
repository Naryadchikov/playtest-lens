# 04: The findings format and a plain report page

**Author:** Muse Code on Muse Wonder (`muse-wonder-1.0`), high effort, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: one module defines and checks `findings.json`, and one script renders a `findings.json` into a plain, self-contained HTML report page. Tested on made-up data. No model call.

Sasha (T3 Code chat, 2026-10-26): "Muse: the findings.json format and a plain report page that renders made-up data, following the change-analyzer skill. Keep the look plain; I'll choose it later from options." And: "No API calls today except cent-sized tests on synthetic input."

Read PLAN.md, "What we build", AGENTS.md, "The analyzer's rules", and follow the `change-analyzer` skill (`.claude/skills/change-analyzer/SKILL.md`).

## Files you own

- `analyzer/findings.py`: the format, one `load(path)` that reads and checks a file and raises a clear `ValueError` naming the bad field
- `report/__init__.py`, `report/render.py`
- `tests/test_findings.py`, `tests/test_report.py`, `tests/fixtures/findings_sample.json`

Touch nothing else (not `analyzer/client.py`, not `analyzer/spark_test.py`). Don't commit.

## The format (the orchestrator's proposal; pure tech, change it if something doesn't fit and say why)

One file per session. Times are seconds into the recording (floats).

```
{
  "format": 1,
  "session": {
    "id": "s01",
    "recording": "s01.mov",
    "duration_s": 840.0,
    "start_flash_s": 2.4 or null
  },
  "findings": [
    {
      "id": "f1",
      "rank": 1 or null (null when dropped),
      "time_s": 312.5,
      "end_s": 442.0 or null,
      "kind": "confused" | "stuck" | "surprised",
      "summary": "one sentence",
      "quote": "the player's words" or null,
      "clip": {"path": "clips/s01/f1.mp4", "start_s": 302.5, "end_s": 322.5} or null,
      "game_state": "what the game was doing" or null,
      "sources": ["spark", "event_log"] (at least one),
      "check": {"verdict": "keep" | "drop", "note": "the evidence", "model": "muse-wonder-1.0"}
    }
  ]
}
```

`load` checks: the format number, required fields and their types, the `kind` and `verdict` values, kept findings have a rank and dropped ones don't, ids are unique, times are within `0..duration_s`. Nothing more.

## The page

- `.venv/bin/python -m report.render <findings.json> -o <page.html>`.
- It calls `analyzer.findings.load`, so the page and the pipeline share one format.
- One self-contained HTML file: inline CSS, no JavaScript framework, no network fetch. Plain: a heading with the session, the kept findings in rank order, then a "Dropped" list. Each finding shows its time (as m:ss), kind, summary, quote, game state, check note, and a `<video>` for its clip (relative path) when it has one.
- **It computes nothing** (AGENTS.md): no ranking, sorting by score, counting or time arithmetic beyond formatting seconds as m:ss. Order comes from the file's `rank`. If the page needs a value, it belongs in the file.
- Escape every string from the file.
- The labels are placeholders; Sasha chooses the look and the words later.

## Made-up data

`tests/fixtures/findings_sample.json`: one invented session, about six findings (kept and dropped, every kind, one without a quote, one without a clip). Obviously fictional: no real people, no real recordings.

## Done means

- `.venv/bin/python -m pytest -q` passes, offline, including the earlier tests.
- Tests cover: `load` accepts the sample and rejects at least a missing `time_s`, a bad `kind`, a duplicate id and a time past the end, each with a clear message; the page shows every finding's summary, quote and m:ss time as in the file; a quote containing `<script>` is escaped; dropped findings appear only under "Dropped".
- The sample renders: show the command and the output path.

## Report back

The files changed, the commands with their output, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Never set, export or read `META_API_KEY` or any credential file. No API call.
- Install Python packages only into this checkout's `.venv`. Prefer the standard library: the page needs no template engine.
- No em dashes or spaced en dashes in anything you write.
- The repo is public: no keys, tokens, recordings or private files.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
