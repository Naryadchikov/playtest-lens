# 22: Grok bot work package (Godot side, on its own VM)

**Author:** Sasha's Grok bot on its own VM, briefed by this text, which Sasha pastes. It has no recordings, no Keychain and no secrets.
**Reviewer:** Grok 4.7 (xhigh, fast) through Cursor, a fresh thread, on what the bot pushes.
**Base:** branch `playtest-lens` of the fork, commit `dc8c771`.

The text below the line is the whole brief. It is meant to be pasted as one message.

---

You are working on a Godot 4.7.2 project, in a loop, without asking questions, until the work package below is finished or blocked. You are the "Grok bot" of Sasha, a game developer. Your job is support work on the Godot side of "Playtest Lens", a hackathon tool that analyzes playtest recordings together with the game's event log. You do not have the analyzer's repo, any recording or any key, and you do not need them.

## The project in 60 seconds

- The test game is Sasha's fork of COGITO (an MIT-licensed first-person game template for Godot): https://github.com/Naryadchikov/cogito-playtest-lens , branch `playtest-lens` (base commit `dc8c771`; `main` of that fork is upstream's and must stay unchanged). Clone it if you have not. Work on a new branch `bot/work` created from `playtest-lens`. Never push to `main` or `playtest-lens`, and never force-push.
- Our code lives in two add-ons: `addons/playtest_lens/` (a passive logger autoload `logger.gd`, `sync_flash.gd`, `telemetry_volume.gd`, headless tests in `tests/`) and `addons/playtest_lens_cogito/` (adapter). The logger writes a JSON-lines session log (schema 1, below). **The add-on is passive: it listens and writes, and never changes gameplay, timing or input.** Do not edit COGITO's own scripts under `addons/cogito/`.
- Use only the **standard** Godot 4.7.2 build (never the Mono/.NET build), stable release, from the official godotengine.org downloads on GitHub. Verify the SHA-512 listed on the release page for the editor and for the export templates before you use them. Export templates for 4.7.2 are needed for work package C. Install them under your own home directory only.
- Headless tests, for example: `godot --headless --path . res://addons/playtest_lens/tests/test_logger.tscn` (each test scene exits 0 on pass). Existing tests: `test_logger.tscn`, `test_sync_flash.tscn`, `test_telemetry_volume.tscn`, and the ones under `addons/playtest_lens_cogito/tests/`. Run them all before you start and after every change. If a test needs a display, use `xvfb-run` and say so.

## Log schema 1 (the contract; one JSON object per line, `t` is seconds from session start)

| event | fields |
|---|---|
| `session_start` | `schema` (1), `session_id`, `wall_time`, `godot_version`, `game_name`, `game_version`, `os`, `renderer`, `log_path` |
| `session_end` | `reason` |
| `sync_flash` | `reason`, sometimes `scene` |
| `scene` | `scene` |
| `position` | `x`, `y`, `z`, sometimes `yaw`, `pitch` (every 0.5 s) |
| `input` | `action`, `pressed` |
| `pause`, `resume` | none |
| `perf` | `fps`, `frame_ms` (once a second) |
| `marker` | none (player pressed F9) |
| `zone_enter`, `zone_exit` | `zone`, `puzzle` |
| `death` | none (from the adapter) |

While the player is inside a telemetry volume every line also carries that volume's `zone` and `puzzle`. Nothing in the log may name a person or a machine (no user names, no home paths, no hostnames).

## How you work (the loop)

1. Do the work packages in order A, B, C, D. For each: make the change, run the whole headless test suite, then commit on `bot/work` with a clear message, and append a short entry to a file `BOT_WORKLOG.md` at the repo root of your branch (what you did, the exact commands, the exit codes).
2. If a package fails twice with different approaches, write down why in `BOT_WORKLOG.md`, skip it and go on. Do not ask Sasha questions while packages remain. Ask only if you are blocked on something that only he can give (an account, a file, a decision), and list all such blockers in one message at the end.
3. Push `bot/work` to the fork if your credentials allow. If they do not, say so in the report and give `git bundle` or `git format-patch` output paths and sizes instead; do not try other routes.
4. When all packages are done or blocked, post the final report (format at the end) and stop.

## Package A: two schema nits from your own earlier retest

Your retest found that `marker` lines in the telemetry test carry an extra `where` field, and that the first `perf` line reads `fps` 1.0 (the counter is not warm yet).
- Look at `logger.gd`. If `where` is the player's current place at the time of the marker and is deliberate, keep it and list its exact contents (field type and example) in the report, so the schema doc can be updated. If it is accidental, remove it.
- Do not emit a `perf` line until the frame counter is warm (for example skip the first second, or skip while `Engine.get_frames_per_second()` is 0 or 1 and the process is under 2 s old), so a cold start never looks like a hitch. Add or adjust a headless test for it.
- Keep every other line exactly as it is. The tests must still pass.

## Package B: a top-down map export for the report

The report page will draw the player's route and a heat map over a top-down picture of each level. The log has `position` lines in world coordinates (`x`, `z` are the ground plane in Godot's Y-up convention; `y` is height). We need, for each of the two COGITO scenes `res://addons/cogito/DemoScenes/COGITO_3_Lobby.tscn` and `COGITO_4_Laboratory.tscn`:
- a PNG, a top-down orthographic view of the level, ceilings hidden (for example by hiding or culling geometry above a height cutoff you choose and document, or by placing the camera below the ceiling with a near plane), floors and walls readable, no HUD, no player, 2048 px on the long side at most;
- a JSON file next to it with exactly: `scene` (res path), `world_min_x`, `world_max_x`, `world_min_z`, `world_max_z` (the area the picture covers, in world units), `px_width`, `px_height`, and `y_cutoff`. A log position (x, z) must map to a pixel with `px = (x - world_min_x) / (world_max_x - world_min_x) * px_width` and `py = (z - world_min_z) / (world_max_z - world_min_z) * px_height` (z grows downward in the picture). State in the JSON that this is the convention.
- one tool script, `tools/map_export.gd` (a `SceneTree` script run with `--script`), that takes the scene path and an output prefix as user arguments after `--`, and a one-line usage comment at the top. Put the two results under `maps/` in the repo (`maps/lobby.png`, `maps/lobby.json`, `maps/laboratory.png`, `maps/laboratory.json`).
- Rendering needs a GPU driver: use `xvfb-run` with the software renderer your VM has (llvmpipe), `--rendering-driver opengl3` or Vulkan lavapipe, whichever works; record the exact command. If rendering cannot work on your VM, fall back to this: the script walks the scene, collects the footprint (the top-down bounding rectangles, or convex hulls when cheap) of every `CollisionShape3D` and `MeshInstance3D` below the height cutoff, and writes them with the same bounds as an SVG (`maps/<name>.svg`) plus the same JSON. Say clearly which path you took.
- Check the result for yourself: open the PNG or SVG and confirm that walls form recognisable rooms. Check the coordinate mapping with one known point: the player's start position in each scene (read it from the scene) must land inside the picture, on a floor.
- The tool must not change either scene file. It runs the scene tree headless-ish and quits; it adds no node to the project permanently.

## Package C: a headless Windows export, and where the log goes

Testers get a Windows build. We need to export it without Sasha's Mac.
- Add `export_presets.cfg` with one preset "Windows Desktop" (x86_64, embed PCK off, console wrapper on, product name "Playtest Build", no icon change, no code signing). Export command to record, headless: `godot --headless --path . --export-release "Windows Desktop" build/PlaytestBuild.exe`. Add `build/` to `.gitignore`. Do not commit the build.
- Verify the export is complete: the folder has the `.exe`, the `.pck` and the console `.exe`; list the PCK's contents (a `godot --headless --main-pack` listing, or `strings`/`unzip -l` style inspection, whichever works) and confirm that `addons/playtest_lens/logger.gd`, `addons/playtest_lens_cogito/adapter.gd`, the two demo scenes and `project.godot` settings for the autoloads are inside. Confirm no folder from your own machine (no home path) is baked in.
- Find out **where the Windows build writes the session log**: read `logger.gd` and the project settings (the `[playtest_lens]` block and the project name) and give the exact path a Windows tester will see, in the form `%APPDATA%\Godot\app_userdata\<project name>\<file name pattern>` or whatever the code really produces. Also say whether a tester can find it easily, and propose (do not implement) a simpler visible location if the default is hard to find.
- Zip the export folder as `PlaytestBuild-windows.zip` and report its size and `sha256sum`. Push is not needed for the zip; if it is under 100 MB commit nothing, just report its path. Sasha will rebuild it himself on the day; what we need from you is the proven recipe and the file list.
- You cannot run a Windows `.exe`; do not try to install Wine for this. Say that the exe was not run.

## Package D: a log validator

Write `tools/validate_log.py` (plain Python 3, standard library only) that reads a session `.jsonl` and prints a short report and exits 0/1:
- every line is valid JSON with numeric `t` and string `event`; `t` never decreases; the first line is `session_start` with `schema` equal to 1; unknown events are counted, not failures;
- for each known event the required fields from the table above are present and of the right type; `position` has numeric `x`, `y`, `z`;
- while inside a zone (between a `zone_enter` and its `zone_exit`) every line carries `zone`, and after the exit none does; `pause` and `resume` alternate;
- no string value anywhere contains a path that looks like a user's home (`/Users/`, `/home/`, `C:\Users\`) or a `@`;
- the report lists the line count per event, the session length, the longest gap between lines, and the first problem found with its line number.
Generate two logs yourself with the existing headless tests (one good, one you corrupt by hand in three ways) and show the validator catching each. Commit the validator and a tiny test `tools/test_validate_log.py` runnable with `python3 tools/test_validate_log.py`.

## Rules (they bind you)

- Never print, write or commit a key, token, password, user name, home path, or any private file. Do not look for any. Do not copy code from any other project of yours or of anyone; COGITO is the only third-party code, MIT, already in the repo.
- No force-push, no history rewrite, no deleting of branches or files outside your own working tree and `build/`. Do not run anything that needs `sudo`. Install only into your own home directory (Godot, export templates).
- No em dashes and no spaced en dashes in anything you write (code comments, commits, the worklog, the report). Use commas, colons, periods or parentheses. English only. Comments short, above the function, in the style of the file you edit.
- Fix what is asked; no refactors, no extra features, no new autoloads, no change to `project.godot` except what a package needs (say what).
- The report must prove things with evidence: commands, exit codes, file paths and sizes. A step you skipped limits the claim: say which.

## Final report format (plain text, at most 40 lines)

1. Per package A to D: DONE, PARTIAL or SKIPPED, in one line each, with the commit hash.
2. The exact commands to reproduce each result (export, map export, validator).
3. Test results: the list of headless tests with exit codes before and after.
4. What `where` is (package A), the Windows log path (package C), the map convention in one sentence (package B).
5. Where the branch is pushed, or the bundle/patch path and size.
6. Blockers or questions for Sasha, numbered, with your recommendation for each.
7. What you did not check.

## What came back

The bot did packages A to D on branch `bot/work` of the fork (commits aee94ef, c10c2d0, 95b8704, eab665d), pushed nothing else, and reported with evidence (its `BOT_WORKLOG.md` is in the fork). Highlights: `where` on marker lines is the telemetry test's own scaffolding, so the logger is unchanged there; the logger writes no perf line until the session is 2 s old (a test checks it); `tools/map_export.gd` renders a top-down PNG plus JSON for the Lobby (1334 x 2048 px) and the Laboratory (2048 x 2016 px) with software rendering under Xvfb and the player start lands on a floor in both; a headless Windows export (62 MB zip, no home path inside, never run); the Windows log path is `%APPDATA%\Godot\app_userdata\Cogito\playtest_lens\<UTC time>.jsonl`; `tools/validate_log.py` with a test, caught three hand-made corruptions on the right lines.

Review: GLM 5.3 on Modal (a different vendor from Grok), fresh, 2026-10-28: PASS, no blockers (docs/reviews/07-bot-work-glm.md). The orchestrator fast-forwarded `playtest-lens` to the bot's commits, ran the six headless Godot tests (all exit 0) and the validator test on this Mac, fixed the one review note (the validator accepted NaN and infinity; commit b0a52cf), added the two `sync_flash` fields to docs/LOG_SCHEMA.md, and copied the maps to `report/maps/`.
