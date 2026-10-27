# 16: Trim the sliding door's open sound

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: the sliding door's open sound lasts about 0.4 s and fades out, instead of running 1.7 s after a 0.3 s slide.

Sasha (T3 Code chat, 2026-10-27): "The door sound: trim it to about 0.4 s with a short fade-out. I'll listen when I'm back."

## What exists

Task 14 set `open_sound` in `addons/cogito/DemoScenes/DemoPrefabs/sliding_door.tscn` to Kenney's `addons/cogito/Assets/Audio/Kenney/stoneDrag4.ogg` (CC0, 1.71 s), which the Lobby also uses elsewhere at full length.

## What to build

- A new file, `addons/cogito/Assets/Audio/sliding_door_open.ogg`: the first 0.4 s of `stoneDrag4.ogg` with a fade-out over its last 0.1 s (ffmpeg `afade`; this ffmpeg has only the built-in `vorbis` encoder, `-c:a vorbis -strict -2`). Keep the source's sample rate and channels if the encoder allows. Leave `stoneDrag4.ogg` as it is.
- `sliding_door.tscn`'s `open_sound` points at the new file. Nothing else changes.

## Files you own (all in `game/`)

- `addons/cogito/Assets/Audio/sliding_door_open.ogg` and its `.import` (new)
- `addons/cogito/DemoScenes/DemoPrefabs/sliding_door.tscn`: the `open_sound` line only

Don't commit.

## Proof

- `ffprobe` of the new file: about 0.40 s. The level over its last 0.05 s is well below the level at 0.1 s (for example `astats` or `volumedetect` on the two windows).
- A headless import and a short headless check that loads `sliding_door.tscn` and prints `open_sound`'s path and length.
- The main menu run (`--quit-after 600`) has no new error compared with `runs/checks/15-run.log`; save it to `runs/checks/16-run.log`.
- `git -C game status --short` shows only the files above.

## Report back

The files changed, the commands with exit codes and output, and what you didn't check (hearing it is Sasha's). No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

Grok 4.7, one run. `sliding_door_open.ogg`: the first 0.4 s of `stoneDrag4.ogg` (Vorbis, 96 kHz stereo, as the source), faded out over the last 0.1 s with a cubic curve (a linear fade left the end within about 1 dB, because the drag gets louder there); RMS -30.5 dB at 0.10 to 0.15 s, -49.4 dB over the last 0.05 s. Godot loads it as 0.400 s; `sliding_door.tscn`'s open sound points at it; the main menu run log is identical to task 15's.

## What the orchestrator changed

Nothing. Read the diff. Committed on the fork's `playtest-lens` as `7ad0f20` and pushed it. Not checked: hearing it (Sasha's, when he's back).
