Reviewer: Grok 4.7 (xhigh), Cursor. Commit `e8511f3fe42ecf81887c50e9c9db8ff86089488e` (the brief commit `974a1b2` is not part of this review). Fork pin `a9f78ac2fcd30e16bce21d73b56d8d105613e8b3`.

**PASS.** Blocking: 0. Should fix: 4. Nits: 3.

## Public rules

Scans were run on the main repo working tree (same tracked files as `e8511f3` except this brief's task file, which has no key) and on the fork commit.

Scan 1, main, the checklist command:

```
grep: game: Is a directory
```

No matching line on stdout. `game` is the submodule gitlink, so grep warns and skips it. A second pass over the 180 real files (same pattern, directories left out) found 0 hits. Fork `git grep` of that pattern at `a9f78ac`: 0 hits.

Scan 2, main: no output. Fork, 5 tracked paths, all licensed game audio:

```
addons/cogito/Assets/Audio/435666__mirkosukovic__alarm-siren.wav
addons/cogito/Assets/Audio/672201__romankolachnik__water_footsteps_02.wav
addons/cogito/Assets/Audio/Phazorknight/Cogito_QuestComplete.wav
addons/cogito/Assets/Audio/Phazorknight/Cogito_QuestFailed.wav
addons/cogito/Assets/Audio/Phazorknight/Cogito_QuestStart.wav
```

No `recordings/` or `runs/` path is tracked in either repo.

Scan 3, `git log --all --format=%ae | sort -u`. Main:

```
26712740+Naryadchikov@users.noreply.github.com
t3code@users.noreply.github.com
```

Fork:

```
26712740+Naryadchikov@users.noreply.github.com
grok-bot@users.noreply.github.com
phazorknight@noreply.codeberg.org
```

Scan 4, main:

```
.gitignore:2:recordings/	recordings
.gitignore:12:runs/	runs
.gitignore:20:.env	.env
.gitignore:43:.claude/skills/modal/	.claude/skills/modal
```

The same command in the fork prints nothing. `game/.gitignore` has no rule for `recordings/`, `runs/`, `.env`, or `*.pem`.

No personal email address in the tracked tree at `e8511f3`. No tracked tester recording. The macOS account name is in two task briefs (should fix 2).

## README against the code

These claims match the code. The one command is `analyzer/analyze.py`: start flash (`tools/video.py:184`, first 120 s), candidate windows of 120 s (`analyzer/analyze.py:28`), check clip of 20 s centred on the moment (`analyzer/check.py:32`, `tools/video.py:90`), prompt gets the transcript and the log slice (`analyzer/check.py:211`), quote kept only when it is in the transcript (`analyzer/check.py:192`), dropped rows keep the checker's note (`report/render.py:1263`). Cache key is a sha256 of the canonical request (`analyzer/client.py:287` and `:321`). Cost lines go to `runs/costs.jsonl` on a real call. Open-weights calls send the video plus a separate wav (`analyzer/client.py:306`); quotes still go through Voice Transcribe (`analyzer/check.py:373`). Default `--out-dir` is `runs/check`. The spatial command in the README matches `analyzer/spatial.py:680`. Watch uses a 30 s trail (`report/render.py:1441`). Friction tags are `by design` for learning and `unplanned` for stuck and blocked (`report/render.py:67`). The learning prompt covers controls, looking around, and a staged twist (`analyzer/prompts/check.md:26`). The add-on listens and writes (`godot/addons/playtest_lens/logger.gd`). `session_start` stores `user://` for the log path, the OS family, and a process id. It does not store a host name or an account name. The table counts in the README were not checked.

## Code health

`.venv/bin/python -m pytest -q`: 249 passed in 44.26 s, exit 0. Offline. No model call.

Findings are written in `analyzer/check.py` after the candidate pass. `analyzer/analyze.py` then calls `report.render`. The page reads `findings.json`. `analyzer/summary.py` annotates `cross_player` and does not create moments. Log candidates join that same check only behind a flag (should fix 1).

## Docs

`README.md`, `AGENTS.md`, and `STATUS.md` agree that Opus writes the code and that the product models are Contributor Spark 1.2, Voice Transcribe, and Muse Spark Open `meta-models/muse-spark-open-1026` on Baseten. `PLAN.md` still has the 2026-10-28 model update that names 1.2 contributor. `docs/PUBLIC_CHECKLIST.md` and `AGENTS.md` agree on the 9:00 PM Eastern deadline. `PLAN.md:77` matches that deadline (03:00 Stockholm on Thu 5 Nov). `STATUS.md:22` does not (should fix 4).

## Should fix

1. `README.md:25` and `PLAN.md:16`. Both say the log adds its own candidate signals (retries, long idle, walking back). `analyzer/analyze.py:70` never passes `--include-log-candidates`. Those candidates are merged only in `analyzer/check.py:346`. The command the README prints does not turn that on. The check still receives the log slice for each Spark moment (`analyzer/check.py:367`).

2. Home path and tester relationship, still in the tree a judge would clone. `docs/tasks/33-prompt-review.md:38` and `docs/tasks/36-report-layout-mocks.md:7` contain `/Users/sashanaria/...`. `DECISIONS.md:257`, `:314`, `:381`, `:383`, `:404` and `docs/tasks/33-prompt-review.md:9` name two testers by who they are to the author and name gitignored recording files. `docs/PUBLIC_CHECKLIST.md` step 9 already says to remove `DECISIONS.md` before the visibility flip. The file is still tracked at `e8511f3`.

3. Who writes the code. `PLAN.md:43` says Claude Sonnet orchestrates and DeepSeek writes the analyzer and the report. `docs/PRIOR_WORK.md:115` says Claude Sonnet 5.5 orchestrates and Grok builds the Godot side. `README.md:83`, `AGENTS.md` ("Who does what"), and `STATUS.md:7` say Opus writes the code, Fable designed the page, Grok reviews, and Sonnet reviews the page.

4. `STATUS.md:22`. "submit by 18:00 CET on Wed 4 Nov (deadline 9:00 PM Eastern)" treats those as one moment. 9:00 PM EST on Wed 4 Nov is 03:00 CET on Thu 5 Nov (`PLAN.md:77`, `docs/PUBLIC_CHECKLIST.md:18`). 18:00 CET on Wednesday is 12:00 EST.

## Nits

1. `README.md:24` says the add-on flashes at New Game and at each level load. The standalone logger flashes when a scene with the player loads (`godot/addons/playtest_lens/logger.gd:162`, reason `level_load`). The New Game flash is the COGITO adapter (`game/addons/playtest_lens_cogito/adapter.gd:89`). `docs/VIDEO_PLAN.md:18` says the add-on flashes once.

2. `PLAN.md:22` still describes open-weights mode as sampled frames plus audio. `analyzer/client.py:306` sends the video file and a separate wav.

3. `AGENTS.md:99` says the one pipeline includes the cross-player summary. `analyzer/analyze.py` ends at the page. Across players is `python -m analyzer.summary --write-cross-player` (`analyzer/summary.py:207`), which the README does not mention. That command does not create a finding.

## What I did not check

- No model call, no Keychain read, no network. No run of `tools/run-analyzer.sh` or `tools/run-baseten.sh`.
- README table lengths, kept and dropped counts, and dollar costs. The brief says those were checked against private files.
- No comparison of a rendered page to a `findings.json`, and no timing check against a recording.
- Godot headless tests were not run on their own. Pytest includes the add-on copy comparison, which passed.
- The fork working tree is dirty and was not reviewed as the commit: `project.godot` only moves the existing `playtest_lens/player_path` block, three untracked `*.uid` files, and an untracked `recordings/` directory. That directory was not opened. It is not in `a9f78ac`. The fork gitignore would not keep a later `git add` from picking it up (should fix, scan 4).
- Demo site, GIF, and page captures are part B.
- Known limits already listed in `docs/FOLLOWUPS.md` were not re-opened. Prompt and threshold changes were out of scope.
- `docs/tasks/`, `docs/reviews/`, `docs/design/`, and `docs/shelved/` were treated as history except the home path and the tester line above.
