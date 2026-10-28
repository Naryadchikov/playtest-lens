# 18: Telemetry volumes (designer zones in the log)

**Author:** Grok 4.7 (xhigh, fast) through Cursor. Directly in `game/` on `playtest-lens`, no worktree.
**Reviewer:** Muse Wonder (other vendor, fresh thread).

## Why

Sasha, T3 Code chat, 2026-10-28: "for being more bullet proof enter and exit can be seperate events, but once we are inside, all other events getting additional params like this zone id, so it is better and easier to post proccess in the future." Zones name the beats in the report (Puzzle, Attempt, Sub-beat grouping, aligned the same day).

## Goal

A designer drags a telemetry volume over a room in the editor, sets two strings, and the session log then knows where the player is:

- `game/addons/playtest_lens/telemetry_volume.gd`: an `Area3D` with `class_name PlaytestLensTelemetryVolume`, exported `zone: String` and `puzzle: String` (both may be empty, puzzle optional). No code needed from the designer beyond placing it and sizing its collision shape.
- The logger (`addons/playtest_lens/logger.gd`) finds volumes in the current scene (group or class scan at scene load, reconnect on scene change), connects `body_entered` and `body_exited` for the player body (the node at `playtest_lens/player_path`), and maintains the set of volumes the player is inside.
- `zone_enter` and `zone_exit` events are logged as separate lines, with `zone` and `puzzle`.
- While the player is inside at least one volume, **every** `log_event` line also carries `zone` and `puzzle` from the most recently entered volume that is still active. Lines outside any volume carry neither field (absence means no zone, never an empty string guess).
- Passive as always: the volume only signals; it never moves, blocks or reads input. Collision monitoring setup must not change gameplay physics for the player (document the expected layer setup in the script header comment: designers put volumes on a layer nothing collides with, monitoring only).

## Tests, headless

Follow the existing test shape in `game/addons/playtest_lens/tests/`:

- A test scene/script placing one volume and moving the player body in and out, asserting: one `zone_enter`, every event while inside carries `zone` (and `puzzle` when set), one `zone_exit`, events after exit carry no `zone`.
- Existing headless tests still pass (logger, flash, adapter, New Game, session).

Run with the standard build only: `/Applications/Godot.app/Contents/MacOS/Godot`. Evidence: the test logs in `runs/` and the command lines. Screenshot is not pass evidence.

## Files you may touch

- `game/addons/playtest_lens/telemetry_volume.gd` (new, plus its `.uid` if Godot writes one)
- `game/addons/playtest_lens/logger.gd`
- `game/addons/playtest_lens/tests/` (new test scene/script only)
- This file, for the outcome section.

Nothing in COGITO's own scripts. Placing volumes in the Lobby or Laboratory scenes is Sasha's step in the editor, not this task.

## Done means

- The headless telemetry test passes and its log shows enter, stamped events, exit, unstamped events.
- `log_event` callers need no changes (adapter included): stamping happens inside `log_event`.
- No new autoload, no project.godot change unless the class registration needs it (class_name should not).

## What came back

Grok 4.7, one run. `PlaytestLensTelemetryVolume` is an Area3D: the designer places it, sets `zone` and `puzzle`, and sizes the collision shape. At runtime the script puts it on no physics layer, turns monitoring on, and turns off monitorable, mouse picking, gravity, damp, and audio overrides. The mask includes every layer, so a player body on layer 5 is seen. The volume only signals.

The logger, on each new current scene, drops the previous volumes (a `zone_exit` for each one still active), then connects `body_entered` and `body_exited` on volumes in that scene. The player is the node at `playtest_lens/player_path`. Enter and exit are their own lines, with `zone` and `puzzle`. While at least one volume is active, `log_event` adds those fields from the most recently entered volume that is still active. Caller fields win, so the enter and exit lines name that volume. Outside, the keys are absent. The adapter was not edited.

Headless `res://addons/playtest_lens/tests/test_telemetry_volume.tscn` exited 0. `runs/checks/18-telemetry.jsonl` shows `zone_enter` (`Puzzle`, `FuseBox`), then a marker and position lines carrying both fields, then `zone_exit`, then a marker and a position with neither field. One stamped position is at x=6.25, just past the box, 7 ms before `zone_exit`: the node had moved, and the area signal followed on the next physics step. Logger, flash, adapter, New Game, and session tests exited 0. Godot wrote `telemetry_volume.gd.uid` and `test_telemetry_volume.gd.uid`. A headless editor quit also moved the `[playtest_lens]` block in `project.godot` without changing the setting; that edit was reverted.

The session test, as it already does, wrote a fresh `runs/checks/15-session.jsonl`. That copy has no `zone` field.

No model API calls on this task. `runs/costs.jsonl` totals about $4.53.

## Outcome (orchestrator)

Grok delivered on 2026-10-28: telemetry_volume.gd, logger stamping inside log_event, headless test. Evidence in runs/checks/18-*. Muse Wonder review: PASS (passive by construction, caller fields win over the stamp, scene change exits every volume, initial overlap caught on the next physics frame). Fork commit 6e4e0ad, pushed. One stamped position lands 7 ms past the volume edge before zone_exit (physics step order); zone borders are good to a frame, not to a millisecond. Overlapping volumes and empty zone strings are untested, listed in docs/FOLLOWUPS.md if Sasha wants them chased.
