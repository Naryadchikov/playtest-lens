# 24: Grok bot work package 2 (scene inventory and volume report)

**Author:** Sasha's Grok bot on its own VM, briefed by this text, which Sasha pastes. It has no recordings, no Keychain and no secrets.
**Proposed by:** the orchestrator (Claude Sonnet 5.5, Claude Code in T3 Code), 2026-10-28. Pure tooling, no design decision in it. Sasha approves before it is pasted.
**Reviewer:** a model from another vendor than the author (GLM or DeepSeek on Modal, or Grok through Cursor), fresh, on what the bot pushes.
**Base:** branch `playtest-lens` of the fork, commit `b0a52cf`.

Why: Sasha places the telemetry volumes (named boxes over rooms and puzzles) in COGITO's Lobby and Laboratory by hand today. These two tools show him where the interactable things are, so he names places from facts, and check his volumes afterwards. The text below the line is the whole brief.

---

You are working on a Godot 4.7.2 project, in a loop, without asking questions, until the work package below is finished or blocked. You are the "Grok bot" of Sasha, a game developer. Your job is support tooling on the Godot side of "Playtest Lens", a hackathon tool that analyzes playtest recordings together with the game's event log. You do not have the analyzer's repo, any recording or any key, and you do not need them.

## Where things are

- Repo: https://github.com/Naryadchikov/cogito-playtest-lens (a fork of the MIT-licensed COGITO template). Pull branch `playtest-lens` (it must contain commit `b0a52cf`; your earlier `BOT_WORKLOG.md`, `tools/map_export.gd`, `tools/validate_log.py` and `maps/` are there). Work on a new branch `bot/work2` from it. Never push to `main` or `playtest-lens`, never force-push.
- Use only the standard Godot 4.7.2 build (never Mono) as before. Do not edit COGITO's own scripts under `addons/cogito/`, and do not change any scene file: your tools read scenes and never save them.
- Our add-on `addons/playtest_lens/` has `telemetry_volume.gd`, a class `PlaytestLensTelemetryVolume` (an Area3D with exported `zone` and `puzzle` strings). Sasha adds such nodes, each with a `CollisionShape3D` child holding a `BoxShape3D`, to the scenes `res://addons/cogito/DemoScenes/COGITO_3_Lobby.tscn` and `COGITO_4_Laboratory.tscn`.
- The maps in `maps/` (`lobby.png`, `lobby.json`, `laboratory.png`, `laboratory.json`) map a world point (x, z) to a pixel with the convention stated in each JSON (`px = (x - world_min_x) / (world_max_x - world_min_x) * px_width`, `py` likewise with z).
- Run the existing headless tests before you start and after every change; they must stay green.

## Package E: scene inventory with an annotated map

Write `tools/scene_inventory.gd` (a `SceneTree` script run with `--script`, arguments after `--`: scene path and output prefix, one-line usage comment on top). It loads the scene, waits a frame, and walks the tree. It lists every node a player can act on or that marks a place: COGITO interactables, doors, switches, buttons, keypads, pickups and inventory items, key and token objects, puzzle pieces, checkpoints, the player's start position, and any `PlaytestLensTelemetryVolume` if present. Find the right classes and groups by reading `addons/cogito/` (do not guess; list in your worklog which classes and groups you matched and why). For each: `name`, `class`, `script` (res path or null), `x`, `y`, `z` (global position), and `parent_path` (the node path inside the scene, never a machine path).
Outputs under `maps/`: `<name>_objects.json` (one array, sorted by name) and `<name>_annotated.svg` (the existing map PNG as the background through a relative `<image href="<name>.png">`, then a numbered marker and a short label per object, colors by kind, a legend, text readable at 2048 px). Mapping from world to pixels must use the map JSON, not a recomputation. Cap labels to avoid pile-ups: when markers fall within 40 px of each other, draw the number only and list the number-to-name pairs in a legend column.
Check yourself: open the SVG as a picture (render it to PNG with any tool you already have, for example Godot's own image import or `rsvg-convert` if present) and confirm that the player start sits on a floor and the numbered objects sit inside the rooms. Run it for both scenes and commit the four result files.

## Package F: a volume report, to run after Sasha has placed volumes

Write `tools/volume_report.gd` (same style): for a scene path it finds every `PlaytestLensTelemetryVolume`, and for each prints `zone`, `puzzle`, the world-space box (min and max x, y, z, taking the node's global transform and its `BoxShape3D` size into account; if the transform is rotated, use the axis-aligned bounds and say so), and the interactables from Package E that sit inside it. It then prints: volumes with an empty zone, two volumes with the same zone and puzzle text but different spellings only by case or spacing (likely typos), volumes that overlap with the overlap size, volumes thinner than 1.6 m in any axis or lower than 1.8 m in height (the player's capsule would not fit), the player start's volume (or "none"), and interactables in no volume. Exit code 0 always; the findings are warnings in plain text. Also write `maps/<name>_volumes.svg` over the map (outlined rectangles with zone labels, same mapping rule as Package E).
Test it without touching Sasha's scenes: make a throwaway copy of a scene under `build/` (git-ignored, create the folder if needed), add three volumes to the copy in code or by editing the copy's text (one fine, one too thin, one overlapping the first), run the tool on the copy, show that it reports exactly those three conditions, then delete only that copy. Add a headless test scene or a small script test if that is simple; otherwise record the proof in your worklog. Do not commit the throwaway copy.

## How you work

Work packages in order E, F. After each: run the whole headless suite, commit on `bot/work2` with a clear message, and append to `BOT_WORKLOG.md` (what you did, the exact commands, the exit codes). If a package fails twice with different approaches, write down why, skip it, go on. Ask nothing while packages remain; list blockers only at the end. Push `bot/work2` to the fork if your credentials allow; otherwise report `git bundle` or `git format-patch` paths and sizes and try no other route.

## Rules

- Never print, write or commit a key, token, password, user name, home path or private file. Nothing in a committed file may contain a machine path (check the JSON and SVG outputs). No code from any other project. No force-push, no history rewrite, no `sudo`, install only under your own home. No em dashes and no spaced en dashes anywhere. English only. Fix what is asked, no refactors, no extra features, no new autoloads, no change to `project.godot`.
- Prove things with commands, exit codes, paths and sizes. A skipped check limits the claim: say which.

## Final report (plain text, at most 30 lines)

1. Package E and F: DONE, PARTIAL or SKIPPED with commit hash. 2. Exact commands. 3. Test results before and after. 4. Which classes and groups counted as interactables, and the object count per scene. 5. Where the branch is pushed (or bundle path and size). 6. Blockers or questions for Sasha, numbered, with your recommendation. 7. What you did not check.
