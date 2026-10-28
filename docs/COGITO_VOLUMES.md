# Placing telemetry volumes in COGITO (Sasha's steps)

Do this on the Mac: the fork is the `game/` folder of this repo, the standard Godot 4.7.2 is installed here, and the commit goes to the fork's `playtest-lens` branch from here. Use the Windows machine later, for the test of the exported build with OBS.

## What a volume is

A box you drag over a room. While the player is inside it, every line in the session log carries the box's `zone` and `puzzle` text. The report then names the section "Area, Puzzle, Attempt" from your words, not from the model's guesses. Leaving and re-entering a box starts the next Attempt.

## See what is where first

The bot's tool drew every door, switch, key, pickup, seat and hint in each level on the map, numbered, with a legend: open `game/maps/lobby_annotated.svg` and `game/maps/laboratory_annotated.svg` in a browser. Use them to choose where a box goes and what to call it (the Lobby has COGITO's own `Hint_*` objects, a natural thing to name a place after). Furniture is in there too (seats, mugs); ignore it.

## Steps

1. Open the project: Godot 4.7.2 (`/Applications/Godot.app`, the standard build), Import, pick `game/project.godot`.
2. Open a level: `addons/cogito/DemoScenes/COGITO_3_Lobby.tscn` (then `COGITO_4_Laboratory.tscn`).
3. Right-click the scene's root node, Add Child Node, search `PlaytestLensTelemetryVolume`, Create. (It is an Area3D that we wrote.)
4. With the new node selected, Add Child Node, `CollisionShape3D`. In the Inspector, set its Shape to a new `BoxShape3D`, and drag the yellow and red gizmo handles so the box covers the room or the puzzle area, from the floor to a little above head height (about 2 m). In the game, any overlap of the player's body with the box counts, so the box has to cover the height the player walks at: not floating above the floor, not shorter than the player, and not so tall that it reaches a balcony or another floor. The volume report is stricter on one point: it counts an object as inside a box by the object's origin, so start the box at or below the floor, or the player start (0.9 m up in the Lobby) and low objects look "in no box". Keep each side at least 1.6 m and the height at least 1.8 m, so the player fits.
5. Select the volume node. In the Inspector set **Zone** (the room or area, for example `Yellow Puzzle Area`) and **Puzzle** (optional, the puzzle inside it, for example `Collect the yellow pieces`). Use the same spelling every time for the same place: matching is exact.
6. Repeat for each room and each puzzle you want named. Keep boxes apart where you can: overlapping boxes work (the latest entered wins) but are not tested.
7. Save each scene (Cmd+S). Do not move, rename or edit anything else in COGITO.

Suggested count: 4 to 8 volumes over the two levels. More is not better: a box per place where a player could get stuck.

## Check the volumes

After you save, tell the orchestrator (or run it yourself): `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --script tools/volume_report.gd -- res://addons/cogito/DemoScenes/COGITO_3_Lobby.tscn res://maps/lobby`. It prints warnings (empty names, near-duplicate spellings, boxes too thin or too low, overlaps, objects in no box) and draws your boxes on `game/maps/lobby_volumes.svg`. It never changes a scene.

## Try it (this is also the first recording we need)

1. Start the screen recording first: Cmd+Shift+5, "Record Entire Screen", Options, microphone on.
2. Run the project (F5). Press **New Game** in the menu: the white flash and beep line the video up with the log.
3. Play for 10 to 15 minutes, thinking out loud like a tester. Press **F9** whenever you feel confused or stuck.
4. Quit the game from the menu (so the log gets its last line), stop the recording.
5. The log is at `~/Library/Application Support/Godot/app_userdata/Cogito/playtest_lens/`, one file per session, newest last. (On Windows it is `%APPDATA%\Godot\app_userdata\Cogito\playtest_lens\`.)
6. Put the video in `recordings/` of this repo (git-ignored) and tell the orchestrator the two file names. It runs the analyzer.

## Commit

In `game/`: `git add` the two scene files, commit on `playtest-lens` and push. Or tell the orchestrator and it does it with the right trailers.
