# 23b: Route, heat, pins, markers and summary computed from the session log

**Author:** DeepSeek V4.1 Flash 1017 on Modal, `tools/run-modal-agent.sh deepseek`, inside worktree `.worktrees/ds-23b` (branch `ds/23b-spatial`).
**Briefed by:** the orchestrator, Claude Sonnet 5.5 in Claude Code in T3 Code, 2026-10-28. **Reviewer:** Grok 4.7 xhigh through Cursor, fresh.
**Base commit:** the commit that adds this file. Runs in parallel with task 23c (cross-player data), which owns `analyzer/summary.py` and does not touch your files.

## Why

The report page (task 23, merged) draws a route, heat spots, numbered pins, F9 markers and a verdict with counts, but only from fields that today's analyzer never writes. The page only renders the file, so the analyzer must compute them from the session log. Sasha, T3 Code chat, 2026-10-28: "you can do your next task, and I will setup volumes on top afterwards". Earlier (DECISIONS.md, editor rendering): "lets do simple version as you suggest first, then we can try and do more in depth later if we have time, yes" (report-side SVG route and heat first).

## Outcome

One new module `analyzer/spatial.py` with `enrich(data, events, video_flash_s)`, which adds to a findings dict, from the session log, the optional fields the page already renders: `route`, `markers`, `summary`, and per kept finding `at`. It makes no model call. `analyzer/check.py` calls it after `assign_beats` whenever `--log` is given (the one path), and `python -m analyzer.spatial <findings.json> --log <session.jsonl> --video-flash-s <seconds> [-o <out.json>]` runs it alone on an existing findings file, so real results can be re-enriched with no API call. It then re-validates with `analyzer.findings.load`.

Read first: `docs/tasks/23-report-redesign.md` (the field shapes), `analyzer/findings.py` (what the loader accepts), `docs/LOG_SCHEMA.md`, `analyzer/log_candidates.py` (`load_log` and the video-time mapping: `video_t = log_t + (video_flash_s - first_sync_flash.t)`, see `find_candidates`) and `analyzer/beats.py` `zone_intervals`. Reuse them; do not copy their code. `AGENTS.md`, "The analyzer's rules", binds you; follow `.claude/skills/change-analyzer/SKILL.md`.

## The fields (all times in video seconds, all coordinates world metres rounded to 2 decimals)

- **Which map.** The log's `scene` lines hold `res://...tscn` paths. `report/maps/<name>.json` each hold a `scene` path. The report draws one map: the one whose scene held the most position lines (time with samples, not count of scenes). `route.scene` is that scene path, `route.map` the map file stem (`lobby`). If no map file matches, write no `route`, no `at`, no `markers` x/z, and print one stderr line saying which scene had no map. Positions logged in other scenes are ignored for `route` and `at`; the limit (one map per report) goes into docs/FOLLOWUPS.md.
- **`route.points`:** `[[t, x, z], ...]` from `position` lines in that scene, in time order, skipping paused time (between `pause` and `resume`) and times before the session's first flash. Downsample so consecutive points are at least 1.0 s apart (always keep the first and the last) so a 15-minute session gives under about 1000 points.
- **`route.heat`:** `[{x, z, r_m, seconds}, ...]`, at most 6, biggest first. Build it from time spent: for each pair of consecutive position samples add `min(dt, 2.0)` seconds to the grid cell (2 m cells) of the earlier sample; merge 8-neighbour cells whose total is at least `HEAT_MIN_S` into one spot (centre of mass x, z, `seconds` the sum, `r_m` the larger of 1.5 and the spot's rms distance from its centre); keep the six longest. Named constants at the top of the module; `HEAT_MIN_S = 15.0`. These numbers are a proposal (Claude Sonnet 5.5), not Sasha's decision: say so in a comment, like `log_candidates.py` does.
- **`at`** on every kept finding: the player's `(x, z)` at `time_s` taken from the nearest position sample within 3.0 s (same scene as the route only). No sample, no `at`. Dropped findings get no `at`. If two pins land within 55 image pixels of each other (use the map JSON for the pixel scale), nudge the later-ranked one by a fixed 60 px step along +x then +y so they stay apart, in world metres; keep it deterministic and test it. Pin positions are a drawing aid, say so in a comment.
- **`markers`:** one per `marker` line (the player pressed F9) in the route's scene: `{t, x, z, moment}`; `x`, `z` from the nearest position sample within 3 s (omit the marker when there is none); `moment` is the `id` of the kept finding with the smallest `|time_s - t|` among those whose span `[time_s - 5, max(end_s, time_s) + 5]` contains `t`, else null.
- **`summary`:** `{verdict, lost_s, counts: {stuck, confused, surprised, suspected_bug}, kept, dropped}`. `counts` are kept findings by `kind`; `kept` and `dropped` counts of verdicts. `lost_s` is the length of the union of the spans `[time_s, end_s]` of kept `stuck` and `confused` findings with an `end_s` (overlaps counted once). `verdict` is one deterministic sentence from a template kept in one `VERDICT` dict at the top of the module (Sasha owns the wording; the page just prints it): `"{kept} moments worth a look: {parts}."` with parts such as `2 stuck, 1 confused` (zero kinds left out, kinds in the order stuck, confused, surprised, suspected bug); with no kept finding: `"No problem moments found."`. Do not name places in it.
- Never overwrite a field the file already has from a model; these fields are written only by this module. Running `enrich` twice gives the same file.

## Files you own

`analyzer/spatial.py` (new), `analyzer/check.py` (only the call, one place, plus the `--log` branch that already exists), `tests/test_spatial.py` (new), `tests/fixtures/spatial_log.jsonl` and `tests/fixtures/spatial_findings.json` (new, fictional, small), `docs/FOLLOWUPS.md` (append). Touch nothing else (not `analyzer/summary.py`, not `analyzer/findings.py` unless a loader check is truly missing, and then say so; not `report/`, not prompts). Do not commit.

## Checks that prove it

1. `../../.venv/bin/python -m pytest -q` passes with no API call.
2. Focused tests: the video-time mapping (a log whose first flash is at t 1.0 and video flash at 4.0 puts a position at log t 11.0 at video 14.0); paused time is skipped; the map choice by position time; no map file gives no `route` and a stderr line; downsampling keeps first and last and spacing of at least 1 s; heat finds a planted 30 s linger and ignores a walk-through; `at` within 3 s and absent beyond; the pin nudge keeps two close pins apart deterministically; marker to moment linking and the null case; `lost_s` with overlapping spans counted once; counts and the verdict sentence for 0 kept, 1 kept and a mix; idempotence; the output loads through `analyzer.findings.load` and renders through `report.render.render_html` (the page then shows the map, pins and tiles).
3. A real-shaped run: `tests/fixtures/session_log.jsonl` is a real-format log from the game; run `python -m analyzer.spatial` on `tests/fixtures/spatial_findings.json` with it (choose a flash time) and show the result renders: write the page to `../../runs/redesign/page-spatial.html` and report its size. Do not call the Meta API.
4. A grep of your diff finds no em dash, no spaced en dash, no key and no path of this machine.

## Done means and report

The tests pass, the CLI works, the one path in `check.py` is wired and the rendered page shows route, heat, pins, markers and tiles from computed data. Report in at most 20 lines: files, commands with exit codes, evidence paths, what you did not check, and anything in this brief you found inconsistent (say so, do not silently change it).
