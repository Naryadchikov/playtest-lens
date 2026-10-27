# 15: Log where the player looks, and nothing that names a person or a machine

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: the log says where the player looks, twice a second, and holds nothing that names a person or a machine. Proven headless, with the scripted session's log redone.

Sasha (T3 Code chat, 2026-10-27): "Also log where the player looks (yaw and pitch, about twice a second), so idle can tell looking around from being away: standing still and looking around is the sign of a lost player." And: "Privacy: fix the log's file path now, before any tester, using the user:// form. Check the whole log for anything else that names a person or a machine."

Follow the `godot-addon-change` skill (`.claude/skills/godot-addon-change/SKILL.md`) and AGENTS.md, "The Godot side".

## What exists

- `addons/playtest_lens/logger.gd`: `position` every 0.5 s with `x`, `y`, `z` and `yaw` (the player body's `global_rotation_degrees.y`). `session_start` has `wall_time`, `godot_version`, `game_name`, `game_version` and `log_path`, today the absolute path, which holds the Mac user name (`/Users/<name>/Library/Application Support/...`).
- COGITO's player turns its body for yaw and its head (`Body/Neck/Head`) for pitch; the camera is `Body/Neck/Head/Eyes/Camera`. Mouse and gamepad looking are read as raw events, not InputMap actions, so they write no `input` lines.
- `addons/playtest_lens_cogito/tests/test_session.gd` (task 12): the scripted Lobby session whose log is the analyzer's fixture.

## What to build

- **Look direction (general add-on):** add `pitch` to the `position` line, and take `yaw` and `pitch` (degrees) from the camera the player sees through (`get_viewport().get_camera_3d()`), so the add-on stays free of COGITO. Same 0.5 s cadence, one line. If there's no camera, write the position without them.
- **The path:** `log_path` becomes the `user://` form (`user://playtest_lens/<file>.jsonl`). Nothing else in the log may hold an absolute path.
- **The check:** go through every event and field the logger and the adapter can write, and the log's file name, and say for each whether it could name a person or a machine (user name, home folder, host name, device id, OS account, hardware). Fix any that do. Report it as a short table.
- **The scripted session:** in the 40 s stand, the player looks around for the first 20 s (turn the body and tilt the head the way COGITO does: a few slow sweeps left and right, and up and down), then keeps the view still for 20 s. Its log is copied to `runs/checks/15-session.jsonl` in the main repo (no longer `12-session.jsonl`).

## Files you own (all in `game/` except the copied log)

- `addons/playtest_lens/logger.gd`, `addons/playtest_lens/tests/`
- `addons/playtest_lens_cogito/adapter.gd` (only if the check finds something), `addons/playtest_lens_cogito/tests/`
- `runs/checks/15-session.jsonl` in the main repo (git-ignored)

Change no COGITO file. Don't commit.

## Proof

- The logger test also checks: `log_path` starts with `user://`; `position` lines have `yaw` and `pitch`, and they follow a stand-in camera turned by the test.
- The session test passes, and its log shows `pitch` and `yaw` changing during the first 20 s of the stand and steady in the last 20 s. Show `grep -c` of `/Users/` and of the Mac's user name and host name (`whoami`, `hostname -s`) in the new log: 0.
- All the other add-on tests still exit 0, and the main menu run (`--quit-after 600`) has no new error compared with `runs/checks/14-run.log`; save it to `runs/checks/15-run.log`.
- `git -C game status --short` shows only the files above.

## Report back

The files changed, the privacy table, the commands with exit codes and output, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.
