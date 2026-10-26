# 06: The logging add-on, general part

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: a passive Godot add-on that writes what the player does as JSON lines, wired into the COGITO demo, with a headless test that proves the lines. It knows nothing about COGITO. The COGITO adapter (task 07) and the start flash and beep (task 08) come next, as separate tasks.

Sasha (T3 Code chat, 2026-10-26): "the logging add-on, as small tasks (the general part, then the COGITO adapter, then the start flash and beep), following the godot-addon-change skill. It no longer waits for the go: a no-go would make the event log more important, not less."

PLAN.md, "The test game": "The logging add-on is a general Godot add-on (inputs, scene changes, player position by node path) with a COGITO adapter (pickups, doors, keypads, quest steps). It writes JSON lines with a timestamp."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`) and AGENTS.md, "The Godot side". The add-on is passive: it listens and writes, and never changes gameplay, timing, input or saves.

## Files you own (all in `game/`)

- `addons/playtest_lens/` (new): `plugin.cfg`, the logger script, its autoload
- `project.godot`: only the lines that enable the plugin and register its autoload, and its settings
- `addons/playtest_lens/tests/`: the headless test scene and script

Change no COGITO file. Don't commit.

## What it logs

One JSON object per line, UTF-8, each with `t` (seconds since the logger started, one monotonic clock: `Time.get_ticks_usec()`) and `event`.

- `session_start`: once, with the wall-clock time (UTC, ISO 8601), the Godot version, the game's name and version from project settings, and the log's absolute path.
- `input`: each InputMap action pressed or released (`action`, `pressed`). Mouse motion is not logged.
- `scene`: when the current scene changes (`scene` = its file path).
- `position`: every 0.5 s while the player node exists (`x`, `y`, `z`, and the facing direction as yaw in degrees). The player is found by a node path set in a project setting, `playtest_lens/player_path`, empty by default; the adapter sets it for COGITO. With no player, no position lines.
- `session_end`: on quit, when Godot gives the chance.

The file goes to `user://playtest_lens/<UTC start time>.jsonl`. Write each line as it happens and flush at least once a second, so a crash loses at most a second.

## Passive means

- Read input in `_input` and never mark it handled; use no `_unhandled_input` that could change who gets an event.
- Never pause, change time scale, move a node, or touch a save file.
- If the log can't be opened, print one clear error and do nothing else; the game runs as before.

## The headless test

`addons/playtest_lens/tests/test_logger.tscn` with a script that, run headless, starts the logger, fires two actions with `Input.parse_input_event`, changes the scene, moves a stand-in player node over a second, quits, then reads the file and checks: every line parses as JSON; `t` never goes down; the input, scene and position lines are there with the right values; `session_start` is first. It exits 0 on pass and 1 on fail, printing what failed.

Command: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game res://addons/playtest_lens/tests/test_logger.tscn`

## Done means

- The test exits 0. Show its output.
- The demo still runs headless (`--quit-after 600`) with no new error compared with `runs/checks/03-run.log`; save the run to `runs/checks/06-run.log`.
- `git -C game diff --stat` shows only the files above.
- Not provable headless (say so, don't fake it): input from a real keyboard and the position of COGITO's player. Task 07 covers the player.

## Report back

The files changed, the commands with exit codes and output, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
