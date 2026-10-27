# 14: Replace the fire sound and the sliding-door sounds, cut the flags

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens`.
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-27.
**Base commit:** this repo and `game/` at the commits named in the prompt.

## Goal

One outcome: the demo no longer uses the five files on docs/PRIOR_WORK.md's "To decide (Sasha)" list, and still runs.

Sasha (T3 Code chat, 2026-10-27): "Yes to all three. Pick the CC0 fire loop yourself, no pick page needed, and credit it in PRIOR_WORK.md." The three were the orchestrator's proposals: a CC0 fire loop in place of the CC BY-NC fireplace sound, Kenney sounds already in the project for the two sliding-door sounds, and cutting the two Freepik flag icons. Read docs/PRIOR_WORK.md, "To decide (Sasha)", for where each file is used.

## The changes

1. **The fire loop.** The orchestrator picked "Fireplace Sound loop" by PagDev, CC0, https://opengameart.org/content/fireplace-sound-loop (file https://opengameart.org/sites/default/files/fire.wav). It's downloaded at `runs/assets/pagdev_fireplace_loop.wav` in the main repo (29.3 s, 44.1 kHz stereo, 32-bit PCM; sha256 `85ca0cc60d0c037fff8b185e31ad1fcdbda6ce45eee17c3ee1318d1b8f59e330`). Convert it to Ogg Vorbis as `game/addons/cogito/Assets/Audio/pagdev_fireplace_loop.ogg` (this ffmpeg has only the built-in `vorbis` encoder: `-c:a vorbis -strict -2`, stereo, 44.1 kHz). Let Godot import it with `loop=true`, as the old file had. Point `audio_burning` in `addons/cogito/Components/Properties/CogitoProperties.tscn` at it.
2. **The sliding door.** In `addons/cogito/DemoScenes/DemoPrefabs/sliding_door.tscn`, set `open_sound` and `close_sound` to Kenney sounds already in `addons/cogito/Assets/Audio/Kenney/` that fit a sliding door. Say which you chose and why.
3. **The flags.** Remove the flag icons from `addons/cogito/Localization/scripts/language_select.gd` and `addons/cogito/EasyMenus/Scenes/OptionsTabMenu.tscn`, so the language picker shows the language names only.
4. After the references are gone, list the five old files (and their `.import` files) that nothing uses any more. Don't delete them: the orchestrator removes them with `git rm` when it commits.

## Files you own (all in `game/`)

- `addons/cogito/Assets/Audio/pagdev_fireplace_loop.ogg` and its `.import` (new)
- `addons/cogito/Components/Properties/CogitoProperties.tscn`, `addons/cogito/DemoScenes/DemoPrefabs/sliding_door.tscn`, `addons/cogito/Localization/scripts/language_select.gd`, `addons/cogito/EasyMenus/Scenes/OptionsTabMenu.tscn`: only the lines above

Nothing in `addons/playtest_lens*`. Don't commit.

## Proof

- `grep -rn "fireburn\|squidge316\|freepik" game --include='*.tscn' --include='*.tres' --include='*.gd' --include='*.cfg' --include='*.godot'` finds nothing.
- A headless import (`--headless --import`) and the main menu run (`--quit-after 600`) have no new error compared with `runs/checks/12-run.log`; save it to `runs/checks/14-run.log`.
- A short headless check that loads `CogitoProperties.tscn` and `sliding_door.tscn` and prints the stream paths it got, and that the fire stream loops.
- In a window, a screenshot of the options menu's language picker, to `runs/checks/14-language.png`.
- All the add-on tests still exit 0.
- `git -C game status --short` shows only the files above.

## Report back

The files changed, the Kenney sounds you chose, the commands with exit codes and output, the screenshot path, the list of now-unused files, and what you didn't check (for example, hearing the sounds). No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, push, or change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.
