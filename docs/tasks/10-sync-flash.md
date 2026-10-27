# 10: The flash and beep at New Game and at each level load

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: the white flash and the beep no longer come once, 1 s after launch. They come when the player presses New Game, and again each time a level loads. Each is logged on the frame it is drawn.

Sasha (T3 Code chat, 2026-10-27): "One change: as far as I know, Windows Game Bar can only start recording once the game window is open, so a flash 1 s after launch would be missed. Make the flash and beep come when the player presses New Game, and again at each level load as extra sync points. Keep 0.25 s white and 1000 Hz."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`) and AGENTS.md, "The Godot side".

## What exists

- `addons/playtest_lens/start_flash.gd` (task 08): a child of the logger that, about 1 s after start, shows a full-window white `CanvasLayer` (layer 128, input ignored) and plays a 1000 Hz beep built in memory, both for 0.25 s, and logs `start_flash` stamped from `RenderingServer.frame_post_draw` (headless: on the next process frame).
- `addons/playtest_lens/logger.gd`: the autoload `PlaytestLensLogger`, with public `log_event(event_name, fields)`; it notices scene changes by polling `get_tree().current_scene`, and finds the player at the `playtest_lens/player_path` setting (`Player` for COGITO).
- `addons/playtest_lens_cogito/adapter.gd`: the autoload `PlaytestLensCogito`, which connects to COGITO's nodes as they enter the tree (`SceneTree.node_added`).
- COGITO's main menu: `addons/cogito/EasyMenus/Scripts/main_menu_controller.gd`, `_on_main_menu_new_game_pressed()` calls `start_new_game()`, which loads the start scene through `CogitoSceneManager.load_next_scene` and a loading screen. Find the New Game button node yourself.

## What to build (the orchestrator's split; tech only)

- **General add-on:** rename `start_flash.gd` to `sync_flash.gd`. No flash at launch any more. The logger gets one public method, `sync_flash(reason: String)`, which shows the flash, plays the beep and logs `{"t": ..., "event": "sync_flash", "reason": ..., "duration_s": 0.25, "beep_hz": 1000}` stamped on the frame the white is drawn, as now. Add other fields only if they help line up (for example `scene` on a level load).
- **Level loads (general):** when the current scene changes to a scene that has the player node at `playtest_lens/player_path`, the logger calls `sync_flash("level_load")`. Scenes without the player (the main menu, the loading screen) get no flash. A reload of the same level (a retry after death) counts as a level load.
- **New Game (the adapter):** the adapter connects to the main menu's New Game button `pressed` signal and calls `PlaytestLensLogger.sync_flash("new_game")`. Edit no COGITO script.
- **Overlap:** if a flash is asked while one is still showing, skip the new one and log nothing for it. Only flashes actually drawn are logged.
- The flash stays passive: input ignored, no pause, no time scale change, nothing in COGITO's state touched.

## Files you own (all in `game/`)

- `addons/playtest_lens/logger.gd`, `addons/playtest_lens/sync_flash.gd` (from `start_flash.gd`, use `git mv`), `addons/playtest_lens/tests/`
- `addons/playtest_lens_cogito/adapter.gd`, `addons/playtest_lens_cogito/tests/`

Change no COGITO file. Don't commit.

## Proof

1. Headless, the logger test: no `sync_flash` in the first 2 s with no player scene; a scene change to a scene with a stand-in player gives exactly one `sync_flash` with `reason` `level_load`; a second call during the 0.25 s gives no second line. Exit 0 on pass, 1 on fail.
2. Headless, the adapter test or a new one: start from COGITO's main menu scene, press its New Game button (emit the button's `pressed`, as a click would), let the start level load, and check the log has `sync_flash` `new_game`, then `scene` for the level, then `sync_flash` `level_load`. Report the time between the two flashes.
3. In a window (not headless), with the standard build: one run from the main menu that presses New Game the same way, saving a screenshot during each flash and one just after, to `runs/checks/10-newgame-flash.png`, `runs/checks/10-level-flash.png`, `runs/checks/10-after.png`, and recording the master bus to check the beep is above silence at each flash. Say plainly if a capture can't run.
4. The existing tests still exit 0, and the main menu run (`--quit-after 600`) has no new error compared with `runs/checks/08-run.log`; save it to `runs/checks/10-run.log`.
5. `git -C game status --short` shows only the files above.

## Report back

The files changed, the New Game button's node path and how you found it, the commands with exit codes and output, the screenshot and log paths, the gap between the two flashes, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

Grok 4.7, one run. `sync_flash.gd` (renamed from `start_flash.gd`) flashes on request through `PlaytestLensLogger.sync_flash(reason)`, queuing the request for the next frame so the line is never stamped before the white is drawn, and drops a request while a flash is showing. The logger calls it with `level_load` (plus `scene`) when a scene with the player loads; the adapter connects to a button named `NewGame` under COGITO's `CogitoMainMenuController` (live path `/root/01_MainMenu/MainMenu/ContentMain/GameMenu/VBoxContainer/MarginContainer2/NewGame`) and calls it with `new_game`. A launch that stays on the main menu doesn't flash. Headless: the flash test and a New Game test from COGITO's real main menu (`new_game`, then the Lobby's `scene`, then `level_load`, 0.87 s apart) pass. In a window: both flash screenshots full white, the one after shows the Lobby, the master bus has the beep at both flashes (peaks 21417 and 28522), 10.7 s between the flashes. The main menu run's errors and warnings match task 08's.

## What the orchestrator changed

Nothing. Read the diff, reran the logger, flash, adapter and New Game tests headless (all exit 0, PASS), looked at `runs/checks/10-newgame-flash.png` and `10-after.png`. Committed on the fork's `playtest-lens` as `cbfb616` and pushed it. Not checked: a retry reloading the same level (task 12 covers it), and a real screen recording lined up with the log.
