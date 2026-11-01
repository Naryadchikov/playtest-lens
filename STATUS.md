# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-31, DECISIONS.md)

Claude Opus 5.5 orchestrates and writes the code. Claude Fable 5.1 made the report's design pass (his pick). A fresh Grok 4.7 xhigh through Cursor reviews code; a fresh Claude Sonnet 5.5 judges captures and the README. Muse Wonder is not called. The Meta pool is for the product's video and audio only. Normal mode: Contributor Spark 1.2. Open mode: Muse Spark Open on Baseten. Table: AGENTS.md.

## Where things stand (2026-11-01, early morning)

- **The report** is rebuilt (tasks 30, 32, 35): both floors, one current moment that the map, clip, timeline and list follow, Top problems first, Play the session (stops at each moment's clip), "Unplanned only", readable game event names, the heat map as its own view. Findings unchanged (0 protected-field differences). Pages: `runs/check/person2-report.html` (Spark) and `person2-report-open.html` (Open); the page he liked before is kept as `person2-report-before-polish.html`.
- **The Godot add-on** lives in this repo (`godot/addons/playtest_lens/`, a real plugin with README and MIT license), with the map tool (`godot/tools/map_export.gd`, one map per floor) and a blank test project. The fork keeps the COGITO adapter, the volumes and a checked copy. Fork `playtest-lens` is `a9f78ac`, pushed. Reviews 19 and 21: PASS.
- **One command:** `tools/run-analyzer.sh analyzer/analyze.py <recording> --log <jsonl>`; a second run on her session made no model call.
- **Tester kit:** `runs/tester-build/PlaytestLens-Cogito-Windows.zip` (build, guide, consent). Needs his task line and one test run on Windows.
- **Drafts for him:** README.md (numbers, no quotes of hers), docs/VIDEO_PLAN.md (his structure, his keypad line).

## In flight

- Reviews 20 (Grok, code) and 22 (Sonnet, captures): both PASS on round 2; Sonnet's S1 and S2 fixed (`877d6ad`), S3 to S7 in FOLLOWUPS.md for the freeze pass.
- Task 36, three new layout mocks by Claude Fable 5.1: done. His pick goes on `runs/check/mock36/compare.html`; then the build into `report/render.py`, reviews, and a new GIF.
- Task 33, the prompt review: his pick (v2 with a friction guard, one prompt for both modes) is on main (`6c4953c`). He judges the 21 cards that changed on `runs/check/prompt33/guard-judge.html`. Then the final reports come with the new layout, README numbers, and he marks the cards.
- Live demo staged, not published while the layout changes (his words, 2026-11-01): `runs/demo-site/site/` (95 MB): `index.html` is his own Lobby session in Spark, `open.html` the same in Open, 33 clips; both came from the cache at $0. He checks the clips for anything private on his editor screen before it goes public.
- README GIF staged (not committed): `runs/demo-site/report.gif` (18 s, 960 px, 7.6 MB) from his session's page.

## Remind Sasha

- Before testers get the build (and when the first tester recording arrives): the consent text now says Meta may train on recordings (contributor mode). Ask whether any tester objects; a tester who does gets the standard model (`muse-spark-1.2`). Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Next (his day plan, DECISIONS.md 2026-10-31)

1. Sun: he reads the page, the README draft and the prompt review; writes the tester task line, tests the zip on Windows, invites testers; gets her consent answer; marks the cards on the page we ship.
2. Mon: tester sessions (held out, blind notes first if he wants a score); cross-player if 2 or more return; final README; video rehearsal.
3. Tue 3 Nov: freeze review (Grok on the repo, Sonnet on README and captures); he records the video.
4. Wed 4 Nov: DECISIONS.md removed with no history, scans, repo public, Pages live, submit by 18:00 CET (deadline 9:00 PM Eastern), X post.

## Open questions for Sasha

1. The 21 changed cards (guard-judge.html), and whether the yellow "Cutscene Trigger" box at 5:17 in her session is meant to be visible.
2. Her consent: public or private, and contributor mode.
3. The tester task line and one run of the zip on Windows.
4. The layout pick, once the three mocks are back. ("by design" stays; nothing is published while we iterate: both his words, 2026-11-01.)

## Credits used

`runs/costs.jsonl` sums to $29.27 on 2026-11-01 (the two guard runs added $5.27): Meta pool calls about $14.6 over the whole project, Baseten about $9.4. Task 33 spent $5.87 of its $8 cap. The Meta pool figure of about $23.90 left was his, on 2026-10-28, not rechecked against Meta's dashboard.
