# 07: The COGITO adapter

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: COGITO's own events reach the Playtest Lens log (pickups, doors, keypads, quest steps), and the player's position is logged in the demo levels. Proven headless.

Sasha (T3 Code chat, 2026-10-26): "the logging add-on, as small tasks (the general part, then the COGITO adapter, then the start flash and beep), following the godot-addon-change skill." PLAN.md: "a COGITO adapter (pickups, doors, keypads, quest steps)". AGENTS.md: "The COGITO adapter subscribes to COGITO's signals and never edits COGITO's own scripts beyond wiring it in."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`).

## What exists

- `addons/playtest_lens/logger.gd`, autoload `PlaytestLensLogger` (task 06): writes `{"t", "event", ...}` lines; `_emit` is private; logs the position of the node at `playtest_lens/player_path` (empty now).
- COGITO signals the orchestrator found (check them, and find the pickup one): `CogitoDoor.door_state_changed(is_open)`, `CogitoDoor.lock_state_changed(is_locked)`, `CogitoKeypad.correct_code_entered`, and on the `CogitoQuestManager` autoload `quest_activated`, `quest_updated`, `quest_completed`, `quest_failed` (each with a `CogitoQuest`). The player is the node `Player` at the root of the level scenes (for example `DemoScenes/COGITO_4_Laboratory.tscn`).

## Files you own (all in `game/`)

- `addons/playtest_lens/logger.gd`: only a small public method for other scripts to write an event, for example `log_event(event_name: String, fields: Dictionary)`, which the private writer uses too (one write path)
- `addons/playtest_lens_cogito/` (new): the adapter script and its headless test
- `project.godot`: the adapter's autoload line, and `playtest_lens/player_path` set to the player's path

The general add-on keeps knowing nothing about COGITO. Change no COGITO file. Don't commit.

## What it logs

- `pickup`: the item's name when the player picks something up.
- `door`: the door's node path and `open` (true/false); `lock`: the door's node path and `locked`.
- `keypad`: the keypad's node path when the right code is entered.
- `quest`: the quest's id or title and the step (`activated`, `updated`, `completed`, `failed`).

Connect to doors and keypads as they enter the tree (`SceneTree.node_added`, or at each scene change), not by editing COGITO's scenes. Use node paths so the analyzer can name the place.

## The headless tests

1. `addons/playtest_lens_cogito/tests/test_adapter.tscn`: instance a COGITO door, a keypad and a pickup from COGITO's own prefab scenes, make each fire its signal (call the method COGITO itself uses, or emit the signal), fire a quest step through `CogitoQuestManager`, then read the log and check the lines. Exit 0 on pass, 1 on fail.
2. Run a demo level directly for a few seconds: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game res://addons/cogito/DemoScenes/COGITO_4_Laboratory.tscn --quit-after 300`, then show that the log has `position` lines.

## Done means

- Both tests and the task 06 test (`res://addons/playtest_lens/tests/test_logger.tscn`) exit 0. Show the output.
- The demo still runs (`--quit-after 600` from the main menu) with no new error compared with `runs/checks/06-run-2.log`; save it to `runs/checks/07-run.log`.
- `git -C game diff --stat` and `git -C game status --short` show only the files above.
- Not provable headless (say so): a real player picking up an item or opening a door with the keyboard.

## Report back

The files changed, the signals you used (and any you couldn't find), the commands with exit codes and output, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
