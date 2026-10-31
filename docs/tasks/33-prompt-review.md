# 33: Prompt review on both sessions, before and after

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Implementer: a Claude Opus 5.5 subagent in its own git worktree. Base commit: `e935d3b` on `main`.

Follow `.claude/skills/change-analyzer/SKILL.md` and `.claude/skills/validate-change/SKILL.md`.

## Why

Sasha, T3 Code chat, 2026-10-31: "also see where we can improve and update prompts for mets models, and maybe rerun the reports both on my and [Player 1's] sessions recordings. maybe there is a real improvement possibility as well."

"maybe" stays his: the current reports are the baseline, and he picks between before and after. Nothing here replaces a page he has.

## The two sessions (private, git-ignored; never copy anything from them into a tracked file)

- **His** (he designed the level's volumes, knows it well): `recordings/cogito/cogito.mp4` (8:32) and `recordings/cogito/2026-10-28T20-31-08Z.jsonl`, start flash 25.2 s.
- **Hers** (first time in the level): `recordings/cogito/cogito_person2.mkv` (21:21) and `recordings/cogito/2026-10-30T12-20-05Z.jsonl`, start flash in `runs/check/person2-findings.json` at `session.start_flash_s`.
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

1. **Worktree setup:** in your worktree root, `ln -s /Users/sashanaria/Documents/CodeProjects/meta-hackathon-v2/runs runs`, the same for `recordings` and `.venv`. The model client caches in `runs/cache/` and logs to `runs/costs.jsonl`, so a call made before is free. Write every new output under `runs/check/prompt33/` and `runs/spark_test/prompt33/` with names that say session, mode and before or after; never overwrite an existing file in `runs/`.
2. **Baselines with today's prompts:** hers already exist (`runs/check/person2-findings.json`, `-open.json`; a rerun should come from the cache at $0: confirm). His need one run per mode with today's prompts (his older findings files used older prompts).
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
