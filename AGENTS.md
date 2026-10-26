# Playtest Lens: rules for agents

A playtest analyst for game developers, built solo by Sasha for the Meta Global AI Developer Hackathon (kickoff 2026-10-26 at 12:00 ET; submissions due 2026-11-04 at 21:00 ET). Read [PLAN.md](PLAN.md) first, then [DECISIONS.md](DECISIONS.md).

Every agent that works here reads this file: the orchestrator, Muse Code, Grok, the reviewers. The rules apply to all of them.

## Who decides

Sasha decides what gets built, every word a user reads, the look, the prompts' goals, and the scope. Agents propose, build what he approved, and prove it works. When unsure, ask him one question instead of deciding.

- [DECISIONS.md](DECISIONS.md) holds his decisions. Each entry is **Decided** (his words quoted, with the date and the channel) or **Proposal** (whose it is). Without his quote, it's a Proposal.
- When he answers, write his words into DECISIONS.md verbatim in the same session. Never turn his "maybe", "for now" or "let's try" into a lock.
- When you give him options, say whose recommendation each one is.

## Hackathon rules that bind the work

- **New work only.** Everything in this repo is made after the kickoff. Third-party code is a clearly separate dependency (COGITO is a git submodule of Sasha's fork) and is listed in [docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).
- **The repo is public.** Never commit a key, a token, a tester's video or audio, or anything private. Check every diff for them before committing.
- **Meta's models are the product.** The analyzer uses the Meta Model API (Muse Spark, Voice Transcribe) and, for the open-weights mode, Muse Spark Open.
- **Out of scope, always:** Sasha's other games and projects, and anything from his employer. Don't copy code from any of them, not even a COGITO fix: redo it in the fork. His other folders on this Mac, including his earlier hackathon folder, are off limits: don't open, read or copy from them.

## Access and cost

- Muse Code runs on Sasha's Muse Code sign-in (his plan), never on the API key. Never read, print or copy its credential files (`~/.config/muse/`).
- **Keep the API key out of every agent's environment.** A `META_API_KEY` in Muse Code's environment takes priority over the sign-in, and would bill Muse's work to the $150 API credits. The key lives only in the macOS Keychain (service `META_API_KEY`). `tools/run-analyzer.sh` reads it from there for the analyzer's own process and nothing else; never export it in a shell profile or with `launchctl`.
- The analyzer calls the Meta Model API from Python. If the key isn't in the Keychain, stop and tell Sasha; never work around it, and never borrow a token from Muse Code's files.
- Never print, log or write a key or token anywhere, and never put one in a URL.
- Every model call goes through one client module. It caches each reply in `runs/cache/` by a hash of the request, so a rerun on the same input costs nothing, and appends one line to `runs/costs.jsonl`: time, model, input and output tokens, cost if returned, and what the call was for. Log Muse Code's usage there too when it's reported. Both are git-ignored.
- The credits are $150. Report the running total in every status message. Stop and ask Sasha before a run you expect to cost more than $10.

## Who does what

Sasha's plan, confirmed in DECISIONS.md on 2026-10-26: "opus on high - orchestrates, muse writes most of the code with grok, sonnet reviews. if it goes poorly, we can switch to more claude code instead". Its aim, in his words: "I might not want spend too much of claude code usage".

| Who | Model and harness | What |
|---|---|---|
| The orchestrator | Claude Opus 5.5, high effort, Claude Code in T3 Code | Plans, briefs, starts and follows the authors, checks their evidence, reads every diff, commits, keeps STATUS.md, brings Sasha results and questions. Writes only small fixes itself |
| Muse Code | Muse Wonder (`muse-wonder-1.0`), high effort, on Sasha's Muse Code plan | Most of the code: the analyzer in Python (the Meta Model API client, the prompts, the pipeline steps, their tests) and the report page |
| Grok | Grok 4.7 (xhigh, fast) through Cursor | The Godot side: the logging add-on, the COGITO adapter, the fork's branch, the Windows export; `tools/verify.py`; the ffmpeg clip tools |
| Code reviewer | Claude Sonnet 5.5, a new subagent each round | Code and tech, at each milestone |
| UX review | Claude Fable 5.1, a new subagent | The report page's captures and the README, once each |
| Freeze review | Claude Opus 5.5, a new subagent, not the orchestrator's thread | Once, the whole repo, at the freeze |
| Sasha | | Decides; judges the findings, the report and the video; plays the build |

Claude models run only through Claude Code, and Grok only through Cursor (Sasha's rule for his projects; it may change).

## When to switch to more Claude

"Goes poorly" means bad software (Sasha's words: "goes poorly that we are getting bad software"). A switch is per area (the analyzer, the report page, the Godot side), not for the whole project. The orchestrator tells Sasha when a trigger trips and asks before switching.

**The quality bar.** The orchestrator checks it at every milestone, with evidence:
- **Right times.** A finding's time matches the video and the event log within 1 second, measured from the start flash in both.
- **Works on a session it wasn't built on.** Once there are two recordings, each milestone runs on one the author never saw, without code changes. Running on a held-out session is fine; reading its notes isn't.
- **Survives real input:** a full-length recording, long silence, another resolution, a log with missing lines. It fails with a clear message, never a wrong answer.
- **The page shows the file.** Three findings picked at random read the same in the report as in `findings.json`.
- **Offline tests pass** with cached replies and no API call.
- **One path,** no duplicated logic, no dead code.

**Switch an area to Claude when:**
- a defect in it reaches Sasha after passing review (a Miss in docs/REVIEW.md), and it's wrong data: a wrong time, a wrong quote, a finding the file doesn't hold; or two Misses of any kind;
- the quality bar fails and the author's fix doesn't pass it;
- Sonnet's review finds the same class of bug again after it was fixed, or blocking correctness findings at two milestones in a row;
- the orchestrator rewrites more than about 20 lines of an author's diff on two tasks in a row.

**Bad findings are a different problem.** If the software works but the model flags the wrong moments, switching authors won't fix it. That's the prompts, the model choice or the idea itself, and it goes to Sasha as the go or no-go question (PLAN.md, the Spark test).

After a switch, Claude Sonnet 5.5 subagents author that area; Opus authors only what Sonnet can't get right. Tool failures aren't a quality switch: when a Grok task fails twice, fallback included, Muse takes it, and the other way round.

## Saving Claude usage

Claude's usage is the budget that runs out first. Muse's plan and the Cursor credits come before it.

- **The orchestrator doesn't author features.** It writes briefs, reads diffs and evidence, and fixes small things (about 20 lines or less). Anything bigger goes back to its author.
- **Short reports.** Authors and reviewers end with the files changed, the commands, the evidence paths and what they didn't check: no file dumps, no recaps. The orchestrator reads a diff, not whole files.
- **A fresh orchestrator thread each day.** At each milestone and at the end of the day, the orchestrator brings [STATUS.md](STATUS.md) up to date: where things stand, what's next, open questions for Sasha, credits used. Sasha starts the next thread with "Read STATUS.md and continue".
- **When an author runs out:** Muse's plan limit resets every five hours and weekly. When it's out, Grok takes the next analyzer task, and Muse takes Grok's when Cursor fails. Claude is the last resort, and says so.
- **Watch the orchestrator's own usage.** If Claude's usage after day 1 runs faster than the nine days allow, tell Sasha: the options are high effort to medium, or Sonnet as orchestrator.

## Working with the authors

- **Start them as T3 Code subagents,** with worktree isolation: Muse on T3's Muse provider, Grok on T3's `cursor` provider. A brief stands alone (see "How to work") and names the skill file the author follows, since only Claude loads `.claude/skills/` by itself.
- **Fallbacks.** Muse: `muse exec` (JSON output, a step cap of 40, the brief as a prompt file; check `muse exec --help` for the current flags), run inside `.worktrees/muse-NN` on a branch `muse/NN-name`. Grok: the Cursor CLI (`cursor-agent`, model `grok-4.7-xhigh-fast`; check `--list-models` and `--help`), run inside `.worktrees/grok-NN`.
- **Never** use `--yolo` or any flag that turns off approvals or the sandbox: this is Sasha's own laptop.
- **Keep Grok's tasks short:** one outcome, about 15 minutes. Cursor ends a run after 10 connection errors and the count never resets, so a long run can die. When a run fails, read its thread before rerunning: the work is often there.
- **Two authors at once only on different files.** Muse owns `analyzer/` and `report/`; Grok owns the Godot side and `tools/`. Each brief lists the files it owns.
- **Brief in a file:** `docs/tasks/NN-name.md`, with the author, the goal, the files it may touch, what "done" means and the evidence to show. After the task, add what came back and what the orchestrator changed. These files are public: they show which agent built what.
- Authors edit files and don't commit. The orchestrator reads the whole diff, runs the checks, and commits it with the author's name and model in a `Co-Authored-By:` trailer next to its own.
- **Asking Muse a question** (for example how the current API takes video) is a read-only task with a small step cap. Check its answer against Meta's docs before building on it.

## The analyzer's rules

- **The findings file is the single truth.** The pipeline writes `findings.json` per session; the report page only renders it and never computes a finding, a time or a count.
- **One path.** Candidates, then the check, then the cross-player summary, in one pipeline. No second way to make a finding.
- **Prompts live in files** (`analyzer/prompts/`), each change committed with the run that motivated it and its before and after findings.
- **Don't tune on the score.** Sasha's blind notes on the sessions held out for the score (PLAN.md) are never read while tuning prompts or thresholds. Tune on the other sessions only.
- Use the `change-analyzer` skill for pipeline and prompt changes (`.claude/skills/change-analyzer/SKILL.md`).

## The Godot side

- The test game is Sasha's COGITO fork, a submodule. Our changes live only on its `playtest-lens` branch: the logging add-on wired in, and the in-game setup documents removed.
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
- Small commits on `main`, each built and tested. No PRs for this solo repo. Don't create the GitHub repo or push until Sasha says so.
- Every commit names the agent and model in a `Co-Authored-By:` trailer, and the harness in a `Harness:` trailer (for example `Harness: Claude Code in T3 Code`).
- **A brief stands alone:** the base commit, one outcome, the files it owns, the checks that prove it, and Sasha's decisions quoted. Two tasks run at once only when they touch different files.
- **T3 Code's tools are the orchestrator's:** it starts the authors and the reviewers with them, reads their threads, and follows their runs. An agent it starts gets a narrower brief: "Do not call any t3-code tools" and "never run rm". A child's approval prompt appears in a thread nobody watches, so on the Mac both once stalled a review for good. If T3 is set to approve a child's calls on its own, Sasha can drop this line.
- Models test first: run the analyzer on the sample session, or play the build, and fix small things before asking Sasha to look.
- When Sasha chooses between looks or wordings, give him a page showing every option side by side, with a "copy my picks" button.

## Writing

- English everywhere.
- No em dashes and no spaced en dashes in anything you write. Use a colon, a comma or parentheses. (Sasha's rule.)
- READMEs and reports lead with the problem in plain words, then the solution.
