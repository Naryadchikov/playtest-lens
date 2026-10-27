# 12: Log deaths, and record a scripted session log

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: the log records the player's death, and one headless run of a real COGITO level writes a log with everything the analyzer's event-log candidates look for, to be its test input.

Sasha (T3 Code chat, 2026-10-27), the task this one feeds (Muse's, next): "The event-log candidates: deaths, retries, long idle stretches and walking back the way you came, read from the logger's JSONL, with log times mapped to video time through the flash. Test on logs from the game's headless tests. No API calls."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`) and AGENTS.md, "The Godot side".

## What exists

- The logger (`addons/playtest_lens/logger.gd`) writes `session_start`, `input`, `scene` (also when the same level is reloaded: a new scene instance), `position` every 0.5 s (`x`, `y`, `z`, `yaw`), `sync_flash` (task 10: `new_game` from the adapter, `level_load` on each scene with the player), `session_end`.
- The adapter (`addons/playtest_lens_cogito/adapter.gd`) logs `door`, `lock`, `keypad`, `pickup`, `quest`.
- COGITO's death: the player's `CogitoHealthAttribute` (found as the player's child attribute named `health`) emits `death()`; the player then calls `player_interaction_component.on_death()` and its HUD opens `DeathScreen` (`addons/cogito/EasyMenus/Scripts/cogito_death_screen.gd`), whose button reloads the last save or starts a new game.

## What to build

- **The adapter:** a `death` line when the player's health attribute emits `death` (with the player's position if it's at hand). Connect the way the adapter connects to doors; edit no COGITO script.
- **A scripted session test** in `addons/playtest_lens_cogito/tests/` (scene and script) that, headless, plays one session the way a person would, in this order, and then copies the log it wrote to `runs/checks/12-session.jsonl` in the main repo (the parent of `game/`):
  1. Starts on COGITO's main menu and presses New Game (as task 10's test does).
  2. In the start level, moves the player about 15 m one way over a few seconds, then about 15 m back along the same line. Moving the player node directly is fine; it's a log for the analyzer, not a physics test.
  3. Stands still with no input for 40 s.
  4. Kills the player through COGITO's own path (damage the health attribute until it emits `death`).
  5. Retries through the death screen's button (emit its `pressed`), which reloads the level.
  6. Moves a few metres, then quits so `session_end` is written.
  The script checks the log has, in order: `sync_flash` `new_game`, `scene`, `sync_flash` `level_load`, `position` lines, `death`, `scene` for the same level, `sync_flash` `level_load`, `session_end`. Exit 0 on pass, 1 on fail.

## Files you own (all in `game/` except the copied log)

- `addons/playtest_lens_cogito/adapter.gd`, `addons/playtest_lens_cogito/tests/`
- `runs/checks/12-session.jsonl` in the main repo (git-ignored; the orchestrator moves it into the analyzer's fixtures)

Change no COGITO file and nothing in `addons/playtest_lens/`. Don't commit.

## Done means

- The session test and the existing tests exit 0. Show the output, and the first and last 5 lines of `runs/checks/12-session.jsonl` plus its line count by event.
- The main menu run (`--quit-after 600`) has no new error compared with `runs/checks/10-run.log`; save it to `runs/checks/12-run.log`.
- `git -C game status --short` shows only the files above.
- Not provable headless (say so): a real player dying from a real hazard.

## Report back

The files changed, the signals you used, the commands with exit codes and output, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

Grok 4.7, one run. The adapter connects `death` on the player's `CogitoHealthAttribute` named `health` and writes `death` with `x`, `y`, `z`. `test_session.gd` presses New Game on the real main menu, slides the player about 10 m out and back in the Lobby, waits 40 s, damages health through `decrease_attribute` until `death`, presses the death screen's button (after New Game it starts a new game, which reloads the Lobby), walks a few metres and quits. 113 lines: 3 `sync_flash` (`new_game`, then `level_load` twice), 3 `scene`, 1 `death`, 99 `position`. All five headless tests exit 0; the main menu run's errors match task 10's. Headless, COGITO's death screen prints a `grab_screenshot` error (no viewport image) and still works.

## What the orchestrator changed

Nothing in the game. Reran the session test (exit 0, PASS). Committed on the fork's `playtest-lens` as `1be0ed4` and pushed it. Copied the log to `tests/fixtures/session_log.jsonl` for task 13, with `session_start`'s `log_path` (an absolute path holding the home folder's user name) replaced by its `user://` form. Not checked: a real death from a real hazard, the death screen's load-a-save branch.
