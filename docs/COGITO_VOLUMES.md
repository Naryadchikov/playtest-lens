# Placing telemetry volumes in COGITO (Sasha's steps)

Do this on the Mac: the fork is the `game/` folder of this repo, the standard Godot 4.7.2 is installed here, and the commit goes to the fork's `playtest-lens` branch from here. Use the Windows machine later, for the test of the exported build with OBS.

## What a volume is

A box you drag over a room. While the player is inside it, every line in the session log carries the box's `zone` and `puzzle` text. The report then names the section "Area, Puzzle, Attempt" from your words, not from the model's guesses. Leaving and re-entering a box starts the next Attempt.

## Steps

1. Open the project: Godot 4.7.2 (`/Applications/Godot.app`, the standard build), Import, pick `game/project.godot`.
2. Open a level: `addons/cogito/DemoScenes/COGITO_3_Lobby.tscn` (then `COGITO_4_Laboratory.tscn`).
3. Right-click the scene's root node, Add Child Node, search `PlaytestLensTelemetryVolume`, Create. (It is an Area3D that we wrote.)
4. With the new node selected, Add Child Node, `CollisionShape3D`. In the Inspector, set its Shape to a new `BoxShape3D`, and drag the yellow and red gizmo handles so the box covers the room or the puzzle area, floor to just above head height. It must not be thin: the player's capsule has to be inside it.
5. Select the volume node. In the Inspector set **Zone** (the room or area, for example `Yellow Puzzle Area`) and **Puzzle** (optional, the puzzle inside it, for example `Collect the yellow pieces`). Use the same spelling every time for the same place: matching is exact.
6. Repeat for each room and each puzzle you want named. Keep boxes apart where you can: overlapping boxes work (the latest entered wins) but are not tested.
7. Save each scene (Cmd+S). Do not move, rename or edit anything else in COGITO.

Suggested count: 4 to 8 volumes over the two levels. More is not better: a box per place where a player could get stuck.

## Try it (this is also the first recording we need)

1. Start the screen recording first: Cmd+Shift+5, "Record Entire Screen", Options, microphone on.
2. Run the project (F5). Press **New Game** in the menu: the white flash and beep line the video up with the log.
3. Play for 10 to 15 minutes, thinking out loud like a tester. Press **F9** whenever you feel confused or stuck.
4. Quit the game from the menu (so the log gets its last line), stop the recording.
5. The log is at `~/Library/Application Support/Godot/app_userdata/Cogito/playtest_lens/`, one file per session, newest last. (On Windows it is `%APPDATA%\Godot\app_userdata\Cogito\playtest_lens\`.)
6. Put the video in `recordings/` of this repo (git-ignored) and tell the orchestrator the two file names. It runs the analyzer.

## Commit

In `game/`: `git add` the two scene files, commit on `playtest-lens` and push. Or tell the orchestrator and it does it with the right trailers.
