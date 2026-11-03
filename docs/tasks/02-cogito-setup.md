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

Sasha's answer (DECISIONS.md, 2026-10-26): "A: a new public GitHub repo under my account, named cogito-playtest-lens." Its `main` is upstream's `main` at `676be6d`, unchanged, with full history; our work goes only on `playtest-lens`.

The orchestrator made it: https://github.com/Naryadchikov/cogito-playtest-lens, with `main` and `playtest-lens` both at `676be6d`, and added it to this repo as a shallow submodule at `game/` on `playtest-lens`. Your checkout already has it. Don't create, change or push to any repo.

## Files you own

- `docs/THIRD_PARTY.md`: only a new section listing the demo assets to check

Touch nothing else. Don't commit anywhere. Godot's import writes `game/.godot/`, which is expected; change no tracked file in `game/`.

## What to do

1. If `game/` is empty, run `git submodule update --init` (shallow, by `.gitmodules`).
2. Import headless, with the standard build only (never `Godot_mono.app`):
   `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --import`
3. Run the main scene briefly: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --quit-after 600`.
4. Save both runs' full output to `runs/checks/02-import.log` and `runs/checks/02-run.log` (git-ignored).
5. List the demo assets that need a license check or credit: models, textures, sounds, music, fonts, shaders, anything not obviously made by Phazorknight. For each: the path, where it says it came from (a license file, a README, a credits file, a comment), the license if stated, and "unknown" if not. Add them as a section "Demo assets to check" in `docs/THIRD_PARTY.md`, facts only.

## Done means

- `git -C game status --short` shows no change to a tracked file.
- The import exits 0, or its failure is reported with the log.
- The run's errors and warnings, deduplicated, each with a count and one example line, in your report. Say which look like the 4.6 to 4.7 move and which look like COGITO's own.
- The asset list in `docs/THIRD_PARTY.md`.

## Report back

The files changed, the commands with their exit codes, the deduplicated errors and warnings, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Use only `/Applications/Godot.app/Contents/MacOS/Godot`.
- Don't change any COGITO file. Don't touch git remote settings, submodule settings or LFS settings.
- Install nothing outside the project.
- No em dashes or spaced en dashes in anything you write.
- The repo is public: no keys, tokens, recordings or private files.

## What came back

Grok 4.7 (xhigh, fast), one run. Import and a 600-frame run of the main scene both exit 0 in 4.7.2.stable.official.ed1daf0bf. Logs in `runs/checks/02-import.log` and `02-run.log` (not in the repo).
- Import: Montserrat font and theme errors on the first import (the theme loaded before the fonts' `.fontdata` existed); the run doesn't repeat them. Exit cleanup lines (4 ObjectDB instances leaked, 2 resources in use) in both.
- Run: COGITO's own `DynamicInputIcon: ISSUE: No rendering device detected.` 49 times, expected headless.
- The move to 4.7: the import rewrote 261 tracked files in `game/` (`project.godot` features `4.6` to `4.7`, new keys in `.import` files). Grok restored them, so the submodule stays at upstream's files.
- The asset list in `docs/THIRD_PARTY.md`, "Demo assets to check". Not read: the Codeberg credits wiki that `game/Readme.md` links to.

## What the orchestrator changed

Nothing. Spot-checked three claims against `game/`: the Kenney prototype textures' `License.txt` (CC0), the credit list's ASSETS lines (Kenney, Quaternius), 18 Montserrat `.ttf` files.
