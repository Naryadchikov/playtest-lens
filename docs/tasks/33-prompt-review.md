# 33: Prompt review on both sessions, before and after

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Implementer: a Claude Opus 5.5 subagent in its own git worktree. Base commit: `e935d3b` on `main`.

Follow `.claude/skills/change-analyzer/SKILL.md` and `.claude/skills/validate-change/SKILL.md`.

## Why

Sasha, T3 Code chat, 2026-10-31: "also see where we can improve and update prompts for mets models, and maybe rerun the reports both on my and [Player 1's] sessions recordings. maybe there is a real improvement possibility as well."

"maybe" stays his: the current reports are the baseline, and he picks between before and after. Nothing here replaces a page he has.

## The two sessions (private, git-ignored; never copy anything from them into a tracked file)

- **His** (he designed the level's volumes, knows it well): `recordings/cogito/cogito.mp4` (8:32) and `recordings/cogito/2026-10-28T20-31-08Z.jsonl`, start flash 25.2 s.
- **Hers** (first time in the level): `recordings/cogito/lobby-player-1.mkv` (21:21) and `recordings/cogito/2026-10-30T12-20-05Z.jsonl`, start flash in `runs/check/lobby-player-1-findings.json` at `session.start_flash_s`.
- Prompts: `analyzer/prompts/spark_test.md` (the candidate pass, video with sound in 120 s windows) and `analyzer/prompts/check.md` (the check: one 20 s clip, its Voice Transcribe text, the log slice, the session outline).
- Modes: normal is `muse-spark-1.2-contributor` through `tools/run-analyzer.sh`; open is `meta-models/muse-spark-open-1026` on Baseten through `tools/run-baseten.sh` (it also reads the Meta key, for Voice Transcribe). The commands are in README.md, "Run it", and in `analyzer/analyze.py` on main once task 30 lands; use the two-step commands (spark_test, then check with `--log` and `--video-flash-s`) with `--out` paths of your own.

## What "right" looks like (Sasha's words; DECISIONS.md has the dates)

- Her Spark page, 2026-10-30: "overall I like Spark report, feels that everything is on point." Of Open: "On Muse Open actually also quite good report." and "Spark was a bit easier to read and anyway havent missed anything." Open was righter that she was stuck on the keypad puzzle while the toilet route meant she was not stuck on progression; that distinction is his sentence for the video, not a new kind (do not add a kind for it). Her Spark cards are the reference: an "after" that loses one of them needs a reason.
- His session, 2026-10-28, on an older report: "lobby, Puzzle 1: lobby_door_unlock" is "just part of the world building", "maybe ok to flag in regards to nice to explain more why it is locked, but not really stuck flag with medium sevirity"; "Archive, Puzzle 13" "should have picked the name of the volume, that is break room"; only the code lock volume has a puzzle line, "so I guess we should stop treating everything as puzzle"; finding the real CEO laptop "could be" another puzzle; the vent unscrewing into the Archive "should be before" the camera and bear trap; the CEO door card is "really wrong": he knew the key could open it and "decided to open it myself with the unlock mechanic and the pin, so I solved it"; the lockpick card: "I have managed to do it without a real struggle"; the Archive entry "was correctly identified" but "is in the end". Check which of these the current prompts already fix before changing anything.
- The report has to be insightful for a level designer (Sasha, 2026-10-31: "making the report easy to use, insightful and strong for hackaton submition").

## Where the orchestrator suspects room (proposals by Claude Opus 5.5; confirm or reject with evidence)

1. **Dilution:** 16 of her 24 kept Spark moments are `friction: learning`, many in the first minutes (controls, a text popup). Is the candidate pass flagging moments a designer would not act on? Can the check say so through friction alone, or does the candidate pass need a sharper line?
2. **Insight:** the cards say what happened, not why or what to look at. Test one small addition in the check's reply: a short, evidence-bound "likely cause in the level" (for example "the keypad gives no hint where the code is"), written only when the clip and log show it, null otherwise. If it holds up, it needs `analyzer/check.py` to keep the field, `analyzer/findings.py` to validate it, and one line in `report/render.py` to show it; build that in your worktree, minimal, so the orchestrator can merge it later.
3. **Placement:** the candidate pass sees no log. Would the session's zone names (the telemetry volumes) in its prompt place moments in the right room more often? Only if it is cheap and stays one path.
4. **Summaries:** every summary starts "Player ...". A summary a designer reads at a glance may name the place and the obstacle first.
5. **Open mode** finds 47 candidates and keeps 33 on her session: is that recall or noise?

Change as little as the evidence needs. Several small prompt edits tested together are fine if the comparison says which one moved what.

## Protocol

1. **Worktree setup:** in your worktree root, `ln -s <main checkout>/runs runs`, the same for `recordings` and `.venv`. The model client caches in `runs/cache/` and logs to `runs/costs.jsonl`, so a call made before is free. Write every new output under `runs/check/prompt33/` and `runs/spark_test/prompt33/` with names that say session, mode and before or after; never overwrite an existing file in `runs/`.
2. **Baselines with today's prompts:** hers already exist (`runs/check/lobby-player-1-findings.json`, `-open.json`; a rerun should come from the cache at $0: confirm). His need one run per mode with today's prompts (his older findings files used older prompts).
3. **After:** edit the prompts (and the minimal code for item 2 if you test it), then run both sessions in both modes.
4. **Compare, per session and mode:** candidates, kept, dropped, kinds, friction; moments matched before and after within 15 s, added, removed; for her Spark run, each reference card kept or lost; for his session, each of his 2026-10-28 points fixed or not. Render before and after pages with `.venv/bin/python -m report.render` into `runs/check/prompt33/`.
5. **Cost cap:** at most $8 of new spend in total (Meta pool plus Baseten); estimate before each run and stop and report if the next run would pass the cap. Report the spend from `runs/costs.jsonl`.

## Rules

- Files you may change, in your worktree only: `analyzer/prompts/*.md`; for item 2 only, `analyzer/check.py`, `analyzer/findings.py`, `report/render.py` and their tests. Never `merge_same_moment`. No second path to a finding.
- Do not call any t3-code tools. Never run rm. Do not commit. Never print, log or copy a key; the two scripts read them for their own process.
- New tester sessions, if any arrive, are held out: never open them or any `notes-*.md` under `recordings/`.
- Tests: `.venv/bin/python -m pytest -q` passes offline in your worktree, with a cached-reply fixture for any new field.

## Report (short)

The prompt diffs and why each; the comparison table; the reference-card and 2026-10-28 checklist; the spend; the page paths for Sasha (before and after, both sessions, both modes); your recommendation, labeled as yours; what you did not check.

## What came back (Claude Opus 5.5 subagent, 2026-11-01)

Not merged: Sasha picks. The change sits uncommitted in the task's worktree (`t3/prompt-review-task-33`), and every page is in `runs/check/prompt33/` (git-ignored).

- **Changed: the check prompt only** (v2). A "cause" line: what in the level likely caused the moment, one short phrase, only when the clip or log shows it, never where a sought object is or what an object can do unless shown (v1 had invented both). The summary starts with the thing in the level, never "Player", at most 20 words. Minimal code: `check.py` keeps `check.cause`, `findings.py` validates it, the page shows a "Likely cause" line (label: a proposal). The candidate prompt is unchanged.
- **Rejected with evidence:** a sharper candidate rule (would cut cards he called on point; the check already tags 16 of 24 as learning); zone names for the candidate pass (every wrong area label falls where no volume was open); Open's extra cards are about half duplicates, a few real (5:49, 21:00, 17:10).
- **Noise:** rerunning the unchanged check on her Spark candidates flips 3 of 24 cards by chance.
- **Results (same candidates everywhere):** her Spark 24 kept before, 24 after (22 matched, the 8:19 vending surprise lost, as in the noise rerun; 5:17 becomes a suspected bug: a debug trigger volume visible in the build); summaries 19 to 13 words; causes on 21 of 24. His session: the lobby door, the CEO door and the lockpick cards he called wrong are gone in Spark before and after; Open v2 rates the lobby door and the key behind glass "blocked", which he called no real struggle.
- **Spend:** $5.87 (Baseten $5.48, Meta about $0.40). Project total $24.00.
- **Its recommendation:** v2 for Spark; the risk to judge is the tilt from "learning" toward "stuck" or "blocked".

## Sasha's pick and the guard (orchestrator, Claude Opus 5.5, 2026-11-01)

Sasha, T3 Code chat, 2026-11-01: "ok, agree with your recomendations, do it this way." The recommendation: one check prompt for both modes, v2 plus a friction guard, because v2 alone pushed moments toward stuck (her Spark 4 to 9 of 24, his Spark 3 to 6 of 8), against his earlier reads (her toilet at 20:04, his fake laptop at 3:03).

- **Ported to main:** the v2 prompt, `check.py` keeps `check.cause`, `findings.py` validates it, one "Likely cause" line on the card in today's `report/render.py` (label a proposal), with the worktree's tests and fixture.
- **The guard** (in `analyzer/prompts/check.md`): friction is judged from what the player does in the clip; learning also covers getting to know a menu or a control, looking around a room out of curiosity, and making sense of a twist the game staged; the cause never changes the friction.
- **First try, discarded:** it also reworded stuck ("repeated failure at the way forward"), and every blocked became stuck (her Spark and Open 0 blocked), which on the page turns High into Medium. Stuck's sentence went back to the original; that run is kept as `*-guard.json`.
- **Final run** (`runs/check/prompt33/*-guard2.json`, same candidates), kept and friction (learning / stuck / blocked):

| Session, mode | Before | Rerun of before (noise) | v2 | v2 with the guard |
|---|---|---|---|---|
| Her Spark | 24: 16 / 4 / 4 | 23: 15 / 5 / 3 | 24: 12 / 9 / 3 | 24: 15 / 7 / 2 |
| Her Open | 33: 24 / 6 / 3 | | 35: 25 / 8 / 2 | 32: 27 / 5 / 0 |
| His Spark | 7: 3 / 3 / 1 | 7: 2 / 4 / 1 | 8: 1 / 6 / 1 | 8: 5 / 2 / 1 |
| His Open | 14: 4 / 8 / 2 | | 12: 2 / 6 / 4 | 13: 6 / 5 / 2 |

  Summaries average 12 to 14 words (19 to 21 before); most kept moments have a cause. Back to by design: her toilet (Open, 20:02), his fake laptop (Open, 3:04 and 3:10), his key in the display case (Open, 1:55), which he called no real struggle. New: her Break Room counters trapping her (Open, 13:11, stuck). Lost: her vending machine surprise (Spark, 8:19), which the noise rerun also lost.
- **Spend:** $2.68 for the first guard run, $2.59 for the final one. Project total $29.27.
- **Waiting for Sasha:** the 21 cards that changed, on `runs/check/prompt33/guard-judge.html` (copy my picks).
