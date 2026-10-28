# Placing telemetry volumes in COGITO (Sasha's steps)

Do this on Windows. Sasha, Cursor chat, 2026-10-28: "can I do all godot work and recording on windows? it is way easier for me" and "yes, you can rewrite things for windows". The analyzer stays on the Mac: the API key is in that machine's Keychain. After you push the scenes, copy the video and the log back, and the orchestrator runs the report there.

Use the standard Godot 4.7.2 build, not the .NET one. Same rule as on the Mac.

## What a volume is

A box you drag over a room. While the player is inside it, every line in the session log carries the box's `zone` and `puzzle` text. The report then names the section "Area, Puzzle, Attempt" from your words, not from the model's guesses. Leaving and re-entering a box starts the next Attempt.

## Get the project

In PowerShell:

```powershell
cd $HOME\Documents
git clone --branch playtest-lens --single-branch https://github.com/Naryadchikov/cogito-playtest-lens.git
cd cogito-playtest-lens
git log -1 --oneline
```

The last line should be `290cba9 Add tools/volume_report.gd and its test; volume_box and find_volumes helpers`. If it is not, stop and tell the orchestrator. Do not use the fork's `main` branch. That branch is an untouched copy of upstream COGITO.

## See what is where first

The bot's tool drew every door, switch, key, pickup, seat and hint in each level on the map, numbered, with a legend: open `maps\lobby_annotated.svg` and `maps\laboratory_annotated.svg` in a browser. Use them to choose where a box goes and what to call it (the Lobby has COGITO's own `Hint_*` objects, a natural thing to name a place after). Furniture is in there too (seats, mugs); ignore it.

## Place the boxes

1. Open the project in Godot 4.7.2 (the standard build). Import, pick `project.godot` in the clone.
2. Open a level: `addons/cogito/DemoScenes/COGITO_3_Lobby.tscn` (then `COGITO_4_Laboratory.tscn`).
3. Right-click the scene's root node, Add Child Node, search `PlaytestLensTelemetryVolume`, Create. (It is an Area3D that we wrote.)
4. With the new node selected, Add Child Node, `CollisionShape3D`. In the Inspector, set its Shape to a new `BoxShape3D`, and drag the yellow and red gizmo handles so the box covers the room or the puzzle area, from the floor to a little above head height (about 2 m). In the game, any overlap of the player's body with the box counts, so the box has to cover the height the player walks at: not floating above the floor, not shorter than the player, and not so tall that it reaches a balcony or another floor. The volume report is stricter on one point: it counts an object as inside a box by the object's origin, so start the box at or below the floor, or the player start (0.9 m up in the Lobby) and low objects look "in no box". Keep each side at least 1.6 m and the height at least 1.8 m, so the player fits.
5. Select the volume node. In the Inspector set **Zone** (the room or area, for example `Yellow Puzzle Area`) and **Puzzle** (optional, the puzzle inside it, for example `Collect the yellow pieces`). Use the same spelling every time for the same place: matching is exact.
6. Repeat for each room and each puzzle you want named. Keep boxes apart where you can: overlapping boxes work (the latest entered wins) but are not tested.
7. Save each scene (Ctrl+S). Do not move, rename or edit anything else in COGITO.

Suggested count: 4 to 8 volumes over the two levels. More is not better: a box per place where a player could get stuck.

Play from the editor (F5) after you save. An exe exported before those saves does not contain the boxes. The export test can be this same Windows machine later.

## Check the volumes

Optional, on Windows, from the clone, using Godot's console executable so the text is visible. Replace the path with where you installed 4.7.2:

```powershell
& "C:\Path\To\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --script tools/volume_report.gd -- res://addons/cogito/DemoScenes/COGITO_3_Lobby.tscn res://maps/lobby
& "C:\Path\To\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --script tools/volume_report.gd -- res://addons/cogito/DemoScenes/COGITO_4_Laboratory.tscn res://maps/laboratory
```

It prints warnings (empty names, near-duplicate spellings, boxes too thin or too low, overlaps, objects in no box) and draws your boxes on `maps\lobby_volumes.svg` and `maps\laboratory_volumes.svg`. It never changes a scene. If you skip this, the orchestrator runs the same check on the Mac after your push.

## Record

1. Start OBS first, with the microphone on, before you press New Game. The white flash and beep have to be in the video.
2. Run the project (F5). Press **New Game** in the menu.
3. Play for 10 to 15 minutes, thinking out loud like a tester. Press **F9** whenever you feel confused or stuck.
4. Quit the game from the menu (so the log gets its last line), then stop OBS.
5. The log is at `%APPDATA%\Godot\app_userdata\Cogito\playtest_lens\`, one file per session, newest last. Paste that path into File Explorer's address bar.
6. Copy the video and that log onto the Mac. Put the video in `recordings/` of the analyzer repo (git-ignored) and tell the orchestrator both file names. Do not commit the video or the log.

## Send the volumes back

From the clone, in PowerShell. Commit only the two scenes. If `git status` shows any other file, stop and send that list before you commit.

```powershell
git status
git diff --stat
git add addons/cogito/DemoScenes/COGITO_3_Lobby.tscn addons/cogito/DemoScenes/COGITO_4_Laboratory.tscn
git commit -m "Place telemetry volumes in the Lobby and the Laboratory."
git push -u origin playtest-lens
git log -1 --oneline
```

The push needs your GitHub login. Send the orchestrator the new commit line. On the Mac, the orchestrator pulls `playtest-lens` and points the analyzer repo's `game/` folder at that commit.
