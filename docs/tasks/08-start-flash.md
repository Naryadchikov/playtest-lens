# 08: The start flash and beep

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: when the game starts, the screen flashes white and a beep plays, once, and the log records the exact moment, so the video and the log can be lined up.

PLAN.md, "What we build": "The game writes an event log as it runs, and flashes white and beeps at the start so the video and the log can be lined up." The `godot-addon-change` skill: "Every line is JSON with a timestamp from one clock, the same one the start flash marks" and "Headless success doesn't prove the start flash or the beep: check those in the running game, with a screenshot."

## The orchestrator's proposal for the numbers (Sasha may change them)

- The flash: the whole window pure white (`#FFFFFF`) for 0.25 s, on top of everything, once, about 1 s after the logger starts (so the window is up and the recording sees it).
- The beep: a 1000 Hz sine, 0.25 s, starting on the same frame. Generate it in code (`AudioStreamGenerator` or a `AudioStreamWAV` built in memory), so there's no new audio asset to license.
- Both are part of the general add-on (`addons/playtest_lens/`), not the COGITO adapter.

## Files you own (all in `game/addons/playtest_lens/`)

- `logger.gd`, or a new `start_flash.gd` it adds as a child: the flash, the beep and the log line
- `tests/`: a test for it

Change no COGITO file and nothing outside `addons/playtest_lens/`. Don't commit.

## What it logs

`{"t": ..., "event": "start_flash", "duration_s": 0.25, "beep_hz": 1000}`, with `t` taken on the frame the white is actually drawn (for example from `RenderingServer.frame_post_draw`), not when the code asks for it. Same clock as every other line.

## Passive means

- The flash is a `CanvasLayer` with a `ColorRect` on top, `mouse_filter` ignore, removed after 0.25 s. It blocks no input and changes no game state, pause or time scale.
- The beep plays on its own `AudioStreamPlayer` and is freed after.

## Proof

1. Headless: a test scene that runs the logger and checks there's exactly one `start_flash` line, after `session_start`, with the fields above. Exit 0 on pass, 1 on fail.
2. In a window (not headless), with the standard build: a short run that saves a screenshot of the viewport during the flash and one just after, to `runs/checks/08-flash.png` and `runs/checks/08-after.png`, and records the master bus (`AudioEffectRecord`) to check the beep's level is above silence around the flash. Say plainly if the audio check can't run.
3. The logger test (`res://addons/playtest_lens/tests/test_logger.tscn`) and the adapter test (`res://addons/playtest_lens_cogito/tests/test_adapter.tscn`) still exit 0; the main menu run (`--quit-after 600`) has no new error compared with `runs/checks/07-run.log`, saved to `runs/checks/08-run.log`.

## Report back

The files changed, the commands with exit codes and output, the screenshot and log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
