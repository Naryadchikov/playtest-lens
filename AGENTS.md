# Playtest Lens: rules for agents

A playtest analyst for game developers, built solo by Sasha for the Meta Global AI Developer Hackathon (kickoff 2026-10-26 at 12:00 ET; building period 2026-10-27 to 2026-11-04; submissions due 2026-11-04 at 9:00 PM Eastern, verified from the Participant Guide, 2026-10-28). Read [PLAN.md](PLAN.md) first, then DECISIONS.md.

DECISIONS.md is Sasha's decision log. It is kept in the working folder only, git-ignored, and is not part of the public repo (Sasha, T3 Code chat, 2026-11-03: "remove decisions from history in remote, leave local copy just for our use"). A fresh clone does not have it.

Every agent that works here reads this file: the orchestrator, the authors, Grok, the reviewers. The rules apply to all of them.

## Who decides

Sasha decides what gets built, every word a user reads, the look, the prompts' goals, and the scope. Agents propose, build what he approved, and prove it works. When unsure, ask him one question instead of deciding.

- DECISIONS.md holds his decisions. Each entry is **Decided** (his words quoted, with the date and the channel) or **Proposal** (whose it is). Without his quote, it's a Proposal.
- When he answers, write his words into DECISIONS.md verbatim in the same session. Never turn his "maybe", "for now" or "let's try" into a lock.
- When you give him options, say whose recommendation each one is.

## Hackathon rules that bind the work

- **New work only.** Everything in this repo is made after the kickoff. Third-party code is a clearly separate dependency (COGITO is a git submodule of Sasha's fork) and is listed in [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md).
- **Everything here is public.** Never commit a key, a token, a tester's video or audio, or anything private. Check every diff for them before committing.
- **Testers are Player 1, Player 2 and so on,** never named or described by who they are to Sasha, in files and in commit messages. Sasha, T3 Code chat, 2026-11-03: "all personal detailes should be removed from history as well, besides mine, it is ok."
- **Meta's models are the product.** The analyzer uses the Meta Model API (Muse Spark, Voice Transcribe) and, for the open-weights mode, Muse Spark Open.
- **Out of scope, always:** Sasha's other projects and anything from his employer. Don't copy code from any of them, not even a COGITO fix: redo it in the fork. Don't open, read or copy from other projects' folders.

## Access and cost

- Muse Code runs on its own sign-in, never on the API key. Never read, print or copy its credential files (`~/.config/muse/`).
- **Keep the API key out of every agent's environment.** A `META_API_KEY` in Muse Code's environment takes priority over the sign-in, and would bill Muse's work to the $150 API credits. The key lives only in the macOS Keychain (service `META_API_KEY`). `tools/run-analyzer.sh` reads it from there for the analyzer's own process and nothing else; never export it in a shell profile or with `launchctl`.
- **The Baseten key follows the same rule as the Meta key:** it lives in the Keychain (service `BASETEN_API_KEY`), and only `tools/run-baseten.sh` reads it, for its own process. Never print, log, write or export it, and never put it in a URL.
- The analyzer calls the Meta Model API from Python. If the key isn't in the Keychain, stop and tell Sasha; never work around it, and never borrow a token from Muse Code's files.
- Never print, log or write a key or token anywhere, and never put one in a URL.
- Every model call goes through one client module. It caches each reply in `runs/cache/` by a hash of the request, so a rerun on the same input costs nothing, and appends one line to `runs/costs.jsonl`: time, model, input and output tokens, cost if returned, and what the call was for. Log Muse Code's usage there too when it's reported. Both are git-ignored.
- The credits are $150. Report the running total in every status message. Stop and ask Sasha before a run you expect to cost more than $10.

## Who does what

The arrangement from 2026-10-31. The authors were different before that: [docs/tasks/README.md](docs/tasks/README.md) and [PLAN.md](PLAN.md).

| Who | Model and harness | What |
|---|---|---|
| Orchestrator and main author | Claude Opus 5.5, Claude Code in T3 Code | Plans, writes the analyzer, the report page, the tools and their tests, keeps STATUS.md and DECISIONS.md, brings Sasha results and questions |
| Code reviewer | Grok 4.7 through Cursor, a fresh reviewer every round; Claude Sonnet 5.5 when Cursor isn't available | Reviews Opus-authored code at milestones and at the freeze |
| Final design pass on the report | Claude Fable 5.1, a Claude Code subagent | Design improvements and UX suggestions on the built page; Grok reviews its code |
| Look reviewer | Claude Sonnet 5.5, a fresh subagent every round | Judges captures of the report page and the README (the UX review in docs/REVIEW.md), and reviews any code Grok authors. The look itself is Sasha's call |
| Grok bot on its own VM | Briefed by prompts Sasha pastes | Parallel work on files nobody else touches, such as the Godot telemetry tool. It has no recordings, no Keychain and no secrets |
| Product, normal mode | Contributor Spark `muse-spark-1.2-contributor` and Voice Transcribe | The Meta credits pay for the product's video and audio processing only (Sasha, 2026-10-28 and 2026-10-31). No agent work is billed to them, and Muse Wonder is not called |
| Product, open-weights mode | Muse Spark Open `meta-models/muse-spark-open-1026` on Baseten (OpenAI-compatible, `https://inference.baseten.co/v1`): the mp4 plus a separate wav, quotes still checked against Voice Transcribe | A separate mode for the open-weights prize; billed to Baseten's credits, not to the Meta credits |
| Sasha | | Decides; judges the findings, the report and the video; plays the build; places the volumes and records on Windows with OBS (steps in docs/COGITO_VOLUMES.md) |

## The quality bar

The orchestrator checks it at every milestone, with evidence:

- **Right times.** A finding's time matches the video and the event log within 1 second, measured from the start flash in both.
- **Works on a session it wasn't built on.** Once there are two recordings, each milestone runs on one the author never saw, without code changes. Running on a held-out session is fine; reading its notes isn't.
- **Survives real input:** a full-length recording, long silence, another resolution, a log with missing lines. It fails with a clear message, never a wrong answer.
- **The page shows the file.** Three findings picked at random read the same in the report as in `findings.json`.
- **Offline tests pass** with cached replies and no API call.
- **One path,** no duplicated logic, no dead code.

## Working with the authors

- **Opus writes in the orchestrator's thread,** or in an Opus subagent with worktree isolation for a task big enough to need its own context. Other agents start as T3 Code subagents with worktree isolation. Once an author's work is committed, the orchestrator removes its worktree without asking. A brief names the skill file the author follows, since only Claude loads `.claude/skills/` by itself.
- **Never** use `--yolo` or any flag that turns off approvals or the sandbox.
- **Keep Grok's tasks short:** one outcome, about 15 minutes. When a run fails, read its thread before rerunning: the work is often there.
- **Brief in a file:** `docs/tasks/NN-name.md`, with the author, the goal, the files it may touch, what "done" means and the evidence to show. After the task, add what came back and what the orchestrator changed. These files are public: they show which agent built what.
- **Short reports.** Authors and reviewers end with the files changed, the commands, the evidence paths and what they didn't check: no file dumps, no recaps.
- Authors other than the orchestrator edit files and don't commit. The orchestrator reads the whole diff, runs the checks, and commits it with the author's name and model in a `Co-Authored-By:` trailer next to its own.
- **Asking a model about an API:** check its answer against the vendor's docs before building on it.

## The analyzer's rules

- **The findings file is the single truth.** The pipeline writes `findings.json` per session; the report page only renders it and never computes a finding, a time or a count.
- **One path.** Candidates, then the check, then the cross-player summary, in one pipeline. No second way to make a finding.
- **Prompts live in files** (`analyzer/prompts/`), each change committed with the run that motivated it and its before and after findings.
- **Don't tune on the score.** Sasha's blind notes on the sessions held out for the score (PLAN.md) are never read while tuning prompts or thresholds. Tune on the other sessions only.
- Use the `change-analyzer` skill for pipeline and prompt changes (`.claude/skills/change-analyzer/SKILL.md`).

## The Godot side

- **Godot is the standard 4.7.2 build only:** `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`. Sasha, T3 Code chat, 2026-10-26: "this project uses only the standard 4.7.2 build, /Applications/Godot.app/Contents/MacOS/Godot, never Godot_mono.app."
- **The add-on's source is this repo:** `godot/addons/playtest_lens/`, with the map tool at `godot/tools/map_export.gd` and a minimal test project in `godot/`. Sasha, T3 Code chat, 2026-10-31: "I agree, lets do B, easier to judge. Once hackaton judging is fninished, we will move it as the seperate thing." Change the add-on here, then copy it to the fork in the same change; `tests/test_godot_addon_copy.py` fails if the two differ.
- The test game is Sasha's COGITO fork, a submodule. Our changes live only on its `playtest-lens` branch: the add-on's copy and the COGITO adapter wired in, the telemetry volumes, and the in-game setup documents removed.
- **The logging add-on is passive.** It listens and writes; it never changes gameplay, timing or input. The COGITO adapter subscribes to COGITO's signals and never edits COGITO's own scripts beyond wiring it in.
- Use the `godot-addon-change` skill for the add-on and the adapter (`.claude/skills/godot-addon-change/SKILL.md`).
- Letting an agent run the game for screenshots and input (the `godot-mcp-runtime` MCP server) is a dev aid that needs Sasha's yes before it's installed. It's never pass or fail evidence.

## Proof, not claims

Every "done" names its evidence: the command, its output or exit code, and a file or screenshot path. A step you skipped limits the claim; say which. Use the `validate-change` skill before calling anything done (`.claude/skills/validate-change/SKILL.md`).

## Reviews

As [docs/REVIEW.md](docs/REVIEW.md) says: a milestone gets a new reviewer on a different model than its author, a report with PASS or NOT PASS, and a stop after round 2 with the approach question for Sasha. Only a reviewer writes PASS.

## How to work

- Fix the case that happened, not every case that could. Prefer the change that deletes or narrows code; list the rest in [docs/FOLLOWUPS.md](docs/FOLLOWUPS.md).
- Never write a polling or sleep loop. Run long jobs in the background and wait with the harness's monitor; say nothing while nothing needs doing.
- Build and test each change before writing the next one.
- Ask Sasha before installing anything outside the project's `.venv`.
- At each milestone, bring `STATUS.md` (kept locally, git-ignored) up to date: where things stand, what's next, open questions for Sasha, credits used.
- Small commits on `main`, each built and tested. No PRs for this solo repo. The GitHub repo is `Naryadchikov/playtest-lens`. When pushing, push only `main`. On the fork, `playtest-lens` is our branch and gets pushed. Sasha, T3 Code chat, 2026-10-26: "“push only main” is about this repo; on the fork, playtest-lens is our branch."
- Every commit names the agent and model in a `Co-Authored-By:` trailer, and the harness in a `Harness:` trailer (for example `Harness: Claude Code in T3 Code`).
- **A brief stands alone:** the base commit, one outcome, the files it owns, the checks that prove it, and Sasha's decisions quoted. Two tasks run at once only when they touch different files.
- **T3 Code's tools are the orchestrator's:** it starts the authors and the reviewers with them, reads their threads, and follows their runs. An agent it starts gets a narrower brief: "Do not call any t3-code tools" and "never run rm". A child's approval prompt appears in a thread nobody watches.
- Models test first: run the analyzer on the sample session, or play the build, and fix small things before asking Sasha to look.
- When Sasha chooses between looks or wordings, give him a page showing every option side by side, with a "copy my picks" button.

## Writing

- English everywhere.
- No em dashes and no spaced en dashes in anything you write. Use a colon, a comma or parentheses. (Sasha's rule.)
- READMEs and reports lead with the problem in plain words, then the solution.
