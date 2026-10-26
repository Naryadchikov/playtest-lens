# 02: COGITO setup

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent with worktree isolation.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: the COGITO demo, from Sasha's fork's `playtest-lens` branch, is a submodule at `game/`, and it imports and runs headless in Godot 4.7.2 with its errors and warnings listed. The logging add-on is not part of this task: it waits for the Spark test's go.

Sasha's words (T3 Code chat, 2026-10-26): "the fork, a playtest-lens branch starting from upstream's main (nothing from any other project on it), and the submodule in this repo at game/ on that branch", then "Open the demo headless in 4.7.2 (import, then run its main scene briefly) and report errors and warnings", and "List the demo assets that need a license check or credit, for docs/PRIOR_WORK.md."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`) where it applies, and AGENTS.md, "The Godot side".

## What the orchestrator found (2026-10-26)

- Upstream COGITO moved from GitHub to Codeberg: https://codeberg.org/Phazorknight/Cogito. `github.com/Phazorknight/Cogito` returns 404.
- Default branch `main`, at `676be6dd6f412c87b391b51593bc4bb356571630` (ahead of tag `1.2.0`). MIT license. No Git LFS. About 1.6 GB.
- `project.godot` targets Godot 4.6; its main scene is `res://addons/cogito/DemoScenes/COGITO_0_MainMenu.tscn`.
- Sasha has no COGITO fork on GitHub yet (`gh repo list`).

## The fork

**Waiting for Sasha's answer:** where the fork lives. The orchestrator fills this in before the task starts. Don't create or change any repo on GitHub or Codeberg until this section names it.

## Files you own

- `.gitmodules` and the `game/` submodule
- `docs/PRIOR_WORK.md`: only a new section listing the demo assets to check
- the fork's `playtest-lens` branch

Touch nothing else in this repo. Don't commit in this repo; commit on the fork's branch only if the brief says so (for this task it doesn't: the branch starts as upstream's `main`, unchanged).

## What to do

1. The fork and the `playtest-lens` branch, from upstream `main` at the commit above, as the section above says. Nothing from any other project on it.
2. Add the submodule: `git submodule add -b playtest-lens <fork URL> game`.
3. Import headless, with the standard build only (never `Godot_mono.app`):
   `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --import`
4. Run the main scene briefly: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --quit-after 600`.
5. Save both runs' full output to `runs/checks/02-import.log` and `runs/checks/02-run.log` (git-ignored).
6. List the demo assets that need a license check or credit: models, textures, sounds, music, fonts, shaders, anything not obviously made by Phazorknight. For each: the path, where it says it came from (a license file, a README, a credits file, a comment), the license if stated, and "unknown" if not. Add them as a section "Demo assets to check" in `docs/PRIOR_WORK.md`, facts only.

## Done means

- `git submodule status` shows `game` at upstream's `main` commit, on branch `playtest-lens`.
- The import exits 0, or its failure is reported with the log.
- The run's errors and warnings, deduplicated, each with a count and one example line, in your report. Say which look like the 4.6 to 4.7 move and which look like COGITO's own.
- The asset list in `docs/PRIOR_WORK.md`.

## Report back

The files changed, the commands with their exit codes, the deduplicated errors and warnings, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Use only `/Applications/Godot.app/Contents/MacOS/Godot`.
- Don't change any COGITO file. Don't touch git remote settings or LFS settings in this repo.
- Install nothing outside the project.
- No em dashes or spaced en dashes in anything you write.
- The repo is public: no keys, tokens, recordings or private files.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
