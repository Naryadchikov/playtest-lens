# 39: The freeze review of the polished bundle

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-01. Base commit: `e8511f3` on `main`. Two reviewers, in parallel, read-only: a fresh Grok 4.7 xhigh (A, the repo) and a fresh Claude Sonnet 5.5 (B, what a judge sees). Each writes only its own report file. Rules for reviews: docs/REVIEW.md. Only a reviewer writes PASS.

## Sasha's words (DECISIONS.md, 2026-11-01, verbatim)

- "I think I am ok with not tweaking it further and polsih things indtead, and review the polished bundle as it is." So: no prompt or threshold changes are in scope; report findings on them only as notes.
- "do everything you can right now in private to prepare all things and verify, do the readme, nice gif, etc."
- "all 3 players are ok with sharing their data, me, [Player 1], [Player 2]."

## A: the repo (Grok 4.7 xhigh), report in `docs/reviews/33-freeze-repo-grok.md`

The repo goes public on Sasha's green light. Review the whole tracked tree at `e8511f3`:
1. **Public rules** (docs/PUBLIC_CHECKLIST.md step 4 and AGENTS.md "Hackathon rules"): run the four scans in step 4 and paste their output; look for keys, tokens, tester media, absolute home paths, personal emails, private names. Recordings and `runs/` must be ignored.
2. **The README tells the truth:** every claim in README.md matches the code (`analyzer/`, `report/render.py`, `tools/`, `godot/addons/playtest_lens/`): the pipeline steps, what the check receives, the quote rule, the cache, the commands and flags, the add-on's behaviour. The numbers in its tables are checked by the orchestrator against private files you cannot see; skip those.
3. **Code health at the freeze:** correctness bugs, dead code, duplicated logic, a second path to a finding (AGENTS.md "The analyzer's rules"). Run `.venv/bin/python -m pytest -q` (offline, no model call) and report the result.
4. **Docs consistency:** README, AGENTS.md, PLAN.md, docs/VIDEO_PLAN.md, docs/PUBLIC_CHECKLIST.md, docs/PRIOR_WORK.md, STATUS.md do not contradict each other or the code. Historical files (docs/tasks, docs/reviews, docs/design, docs/shelved) are history: flag only what would mislead a judge.

## B: what a judge sees (Claude Sonnet 5.5, high), report in `docs/reviews/34-freeze-judge-view-sonnet.md`

A judge reads the README, opens the live demo and maybe watches the GIF, in a few minutes. Score the experience from 1 to 10 (PASS at 8.5 or more, as in reviews 26 to 29) with evidence:
1. **README.md**: does a game developer get the problem, the solution and why Meta's models matter in 30 seconds? Is anything unclear, overclaimed, too long or missing? The rubric: Impact 30%, Use of Meta AI tooling 25%, Technical depth 20%, Demo 25%. Words are Sasha's call: propose, don't rewrite.
2. **The demo site**, served at `http://127.0.0.1:8765/` (the orchestrator runs it; the files are `runs/demo-site/site/`): the front page, `lobby-player-1.html`, `lobby-player-1-open.html`, `lobby-player-2.html`. Capture at 1920 x 1080 dark, 1440 x 900 light and 390 px, in Chromium and WebKit (`PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I <script>`; never `playwright install`). Put captures in `/tmp/t39/`.
3. **The GIF** (`runs/demo-site/site/report.gif`): does it show the product in 20 seconds without explanation? Look at frames (ffmpeg is installed).
4. The page design itself passed at 8.9 (review 29); judge it again only where it hurts a judge's first minutes.

## Rules for both

- Read-only except your own report file. Do not commit. Do not call any t3-code tools. Never run rm. No model calls, no network beyond `127.0.0.1`, no Keychain. Never copy anything from `runs/` or `recordings/` into a tracked file. Only stop processes you started, never by name. No em dashes and no spaced en dashes.
- Report: PASS or NOT PASS, findings ranked (blocking, should fix, nit), each with file and line or a capture path, and what you did not check. Short.
