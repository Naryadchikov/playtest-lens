# What existed before the hackathon

The hackathon's rule: what's presented must be built during the event, and what existed before must be clearly identified.

## Third-party

- **COGITO** by Phazorknight (MIT), the immersive-sim template whose demo is the test game. Origin: codeberg.org/Phazorknight/Cogito at 676be6d (MIT). The author's copy, [github.com/Naryadchikov/cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens), keeps upstream's `main` at that commit, unchanged, with its full history. Our changes are only the commits on its `playtest-lens` branch; the main ones are listed below. It's the submodule at `game/`.
- **Godot 4.7.2**, **Python**, **ffmpeg**, and any library listed in the analyzer's requirements file.
- Demo asset credits: listed here once each asset's license is checked.
- Tools used to build it, not part of the submission: T3 Code, Claude Code, Muse Code and Cursor.

## Demo assets to check

From the COGITO checkout at 676be6d (`game/`). Each license below is from a file in that checkout, from the credits page `game/Readme.md` links to, or from a page that page or a local readme links. Credits page: https://codeberg.org/Phazorknight/Cogito/wiki/Credits%2C-Contributors%2C-License (raw text, read 2026-10-26). "The MIT line" below means this sentence on that page: "All other included assets either made by Philip Drobar or one of the contributors, published under MIT License." "Unknown" means none of these sources states one license for that item.

Kenney items use https://kenney.nl/support, which says: "Yes, all game assets on the asset pages are public domain licensed (CC0)." The same page says attribution is not required, and that a credit, if given, is the word "Kenney". It says not to use the Kenney logo.

- `game/addons/cogito/Assets/Textures/Prototype Textures/` (80 PNG files and `License.txt`). Source: `License.txt` in that folder, Kenney (www.kenney.nl), dated 08-04-2020, and https://kenney.nl/support. License: CC0 (Creative Commons Zero) 1.0, http://creativecommons.org/publicdomain/zero/1.0/. `License.txt` says: "Support us by crediting Kenney or www.kenney.nl (this is not mandatory)."
- `game/addons/cogito/Assets/Models/Kenney/` (252 `.glb` files: `barrel.glb`, `bag.glb`, `toolPickaxe.glb`, `chest.glb`, plus the Blaster, Furniture, and SpaceInterior packs). Source: the credits page ("3D models are by Kenney", https://www.kenney.nl/) and https://kenney.nl/support. `barrel.glb` names generator UniGLTF-2.34.0 and has no license field. License: CC0. Attribution is not required.
- `game/addons/cogito/Assets/Audio/Kenney/` (57 `.ogg` and `.wav` files, including Impacts, VoiceFemale, Footsteps, and UiAudio). Source: the credits page (audio by Kenney, https://www.kenney.nl/) and https://kenney.nl/support. License: CC0. Attribution is not required.
- `game/addons/cogito/Assets/Graphics/Crosshair_Kenney/` (6 PNG files). Source: the folder name and https://kenney.nl/support. License: CC0. Attribution is not required.
- `game/addons/cogito/Assets/Graphics/InputIcons/InputIconSheet_Kenney_Xbox.png`, `InputIconSheet_Kenney_SteamDeck.png`, `InputIconSheet_Kenney_KeyboardMouse.png`, `InputIconSheet_Kenney_PS.png`. Source: the file names and https://kenney.nl/support. License: CC0. Attribution is not required.
- `game/addons/cogito/Assets/Graphics/InputIcons/InputIconSheet_Gamepad.png`. Source: the credits page's MIT line. The page does not name this file, and the file name does not say Kenney. License: MIT. Author on that line: Philip Drobar (https://www.philipdrobar.com/) or a contributor. Notice: see Credit lines.
- Quaternius. Source: the credits page, "NPC animations are by Quaternius (https://quaternius.itch.io/universal-animation-library/) under CC0". That itch page says "Free to use in personal, educational and commercial projects. (CC0 License)" and "Asset license Creative Commons Zero v1.0". `game/addons/cogito/Assets/UniversalAnimationLibrary/AnimationLibrary_Godot_Standard.glb` is the only file in that folder. Its glTF generator is Khronos glTF Blender I/O v4.3.47, with no copyright or license field. `game/addons/cogito/PackedScenes/cogito_player_advanced.tscn` embeds a resource named `AnimationLibrary_Godot_Standard_Mannequin`. License: CC0. Attribution is not required.
- `game/addons/cogito/Assets/Fonts/Montserrat/` (18 `.ttf` files). Source: the name table of `Montserrat-Regular.ttf`. Copyright in that table: "Copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat)". Designer and manufacturer: Julieta Ulanovsky. License, in that table: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL". The folder had no separate license file; `OFL.txt` with the 2011 copyright line and the full OFL 1.1 text sits next to the fonts on `playtest-lens` (added after task 05). The name table has no trademark record and the word Reserved does not appear in it. The current `OFL.txt` on https://github.com/JulietaUla/Montserrat says "Copyright 2024 The Montserrat.Git Project Authors (https://github.com/JulietaUla/Montserrat.git)" and names no reserved font name in its copyright header. The notice for the files in this checkout is the 2011 line in the font. See Credit lines.
- `game/addons/cogito/Assets/hdris/kloofendal_48d_partly_cloudy_puresky_2k.hdr`. Source: the credits page, "Cloud HDR (kloofendal_48d_partly_cloudy_puresky)2k.hdr by Greg Zaal, used under CC0." The Poly Haven page https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky says CC0, lists authors Greg Zaal (original) and Jarod Guest (sky edits), and describes it as an edited sky-only version of Kloofendal 48d Partly Cloudy. License: CC0. Attribution is not required.
- Sounds the credits page names, each opened on Freesound on 2026-10-26. The credits page and the Freesound page name the same license on every one of these. A Creative Commons 0 page says: "You can copy, modify, distribute and perform the sound, even for commercial purposes, all without the need of asking permission to the author." Those pages link to http://creativecommons.org/publicdomain/zero/1.0/. Attribution is not required on the CC0 files. The CC BY lines are under Credit lines.
  - `game/addons/cogito/Assets/Audio/241842_poyekhali_running-water.ogg`. Running Water by Poyekhali, https://freesound.org/s/241842/. License: Attribution 3.0, http://creativecommons.org/licenses/by/3.0/.
  - `game/addons/cogito/Assets/Audio/435666__mirkosukovic__alarm-siren.wav`. Alarm Siren.wav by mirkosukovic, https://freesound.org/s/435666/. License: Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.
  - `game/addons/cogito/Assets/Audio/524306_bertsz_flame_ignite.ogg`. Match strike by Bertsz, https://freesound.org/s/524306/. License: Creative Commons 0.
  - `game/addons/cogito/Assets/Audio/537275__laughingfish78__dirt-sliding.ogg`. Dirt Sliding.wav by Laughingfish78, https://freesound.org/s/537275/. License: Creative Commons 0.
  - `game/addons/cogito/Assets/Audio/pagdev_fireplace_loop.ogg` (added in `1a381f1`, in place of `641848_newlocknew_fireburn.ogg`, which was CC BY-NC 4.0 and is removed). Fireplace Sound loop by PagDev, https://opengameart.org/content/fireplace-sound-loop (file `fire.wav`, converted to Ogg Vorbis, stereo, 44.1 kHz, looping). License: CC0, https://creativecommons.org/publicdomain/zero/1.0/. The page says "Credit is not required, but it is always appreciated."
  - `game/addons/cogito/Assets/Audio/651743__department64__underwater-deep-water-loop.ogg`. Underwater Deep Water Loop by Department64, https://freesound.org/s/651743/. License: Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.
  - `game/addons/cogito/Assets/Audio/666290_ekrcoaster_water_hot_surface_short.ogg`. Water steaming on hot surface #1 by Ekrcoaster, https://freesound.org/s/666290/. License: Creative Commons 0.
  - `game/addons/cogito/Assets/Audio/672201__romankolachnik__water_footsteps_02.wav`. Footsteps_02.wav by RomanKolachnik, https://freesound.org/s/672201/. License: Creative Commons 0.
- `squidge316_sliding-door_01.ogg` and `squidge316_sliding-door_02.ogg` (license unknown) were removed in `1a381f1`. `sliding_door.tscn` now uses `sliding_door_open.ogg` (the first 0.4 s of Kenney's `Kenney/stoneDrag4.ogg`, faded out; `7ad0f20`) (open) and `Kenney/metalLatch.ogg` (close), CC0 like the other Kenney files.
- `game/addons/cogito/DynamicFootstepSystem/Assets/Audio/` (Dirt, Grass, Stone, Wood, four `.ogg` files each). Source: `game/addons/cogito/DynamicFootstepSystem/Readme.md`, by AC-Arcana, and the four Freesound pages, read 2026-10-26. The readme says all sounds in the DynamicFootstepSystem are CC0 from freesound.org, with one URL per surface. Each of those pages says Creative Commons 0 and links to http://creativecommons.org/publicdomain/zero/1.0/. License: CC0. Attribution is not required. The readme gives one upload for each surface, and each surface folder holds four files.
  - Dirt: Footsteps Dirt Road 1.wav by HenKonen, https://freesound.org/people/HenKonen/sounds/682127/
  - Grass: Footsteps Grass.wav by HenKonen, https://freesound.org/people/HenKonen/sounds/682128/
  - Stone: Footstep.WAV by xmike80x, https://freesound.org/people/xmike80x/sounds/706207/
  - Wood: "Footsteps, Solid Wood Rug, Male Boots, Medium Pace and Scuffs.wav" by SpliceSound, https://freesound.org/people/SpliceSound/sounds/150444/
- `game/addons/cogito/Assets/Audio/HourOfOblivion/` (`bark_chase.ogg`, `bark_endsearch.ogg`, `bark_investigate.ogg`, `bark_search.ogg`). Source: the credits page's MIT line. The page lists HourOfOblivion as a contributor (CogitoNPC and player detection) and does not name these files. The folder name matches that contributor. License: MIT. Notice: see Credit lines.
- Pixabay sounds the credits page names. The local file names match those titles. The files were not played. Each sound page says "Free for use under the Pixabay Content License". The summary at https://pixabay.com/service/license-summary/ says you may use the content for free, without attributing the author, and may modify or adapt it. It forbids selling or distributing the content on a standalone basis: where no creative effort has been applied and it stays in substantially the same form as on Pixabay. The summary says only the full Content License is legally binding. That full text was not read.
  - `game/addons/cogito/Assets/Audio/Spray.ogg`. The credits page says "Spray by RibhavAgrawal", https://pixabay.com/sound-effects/spray-185000/. That page's title is "Spray by VoiceBosch". The page also includes this note: "You are welcome to use these sound effects in your commercial projects. However, selling/distributing these sound effects in their original form for commercial gain or claiming ownership over them is prohibited. You do not have permission to replicate the voices featured on SoundBiter SFX through the use of AI technology."
  - `game/addons/cogito/Assets/Audio/SodaOpen_EnergyDrinkEffect.ogg`. The credits page says "Energy Drink by VoiceBosch", https://pixabay.com/sound-effects/energy-drink-effect-230559/. That page's title is "energy drink effect by RibhavAgrawal".
  - `game/addons/cogito/Assets/Audio/SodaOpen.ogg`. The credits page says "Soda Can Open by OxidVideos", https://pixabay.com/sound-effects/soda-can-open-183214/. That page's title is "Soda can open by OxidVideos". OxidVideos's note on the page says the sounds may be used in commercial and personal projects, and that credit is not required.
- `game/addons/cogito/Assets/Audio/vending_machine_sfx.ogg`. Source: the credits page's MIT line. The page does not name this file. License: MIT. Notice: see Credit lines.
- `freepik_flag_de.png` and `freepik_flag_us.png` (license unknown) were removed in `1a381f1`. The language picker shows the language names without icons.
- `game/addons/cogito/Assets/Models/shelf_base.glb`, `shelf_drawer.glb`, `ladder.glb`, `pistol.glb`, `target.glb`. Source: the credits page, "3D models are by Kenney (https://www.kenney.nl/) or Philip Drobar (https://www.philipdrobar.com/)", and the MIT line. These files sit outside `Assets/Models/Kenney/` and have no Kenney name. The glTF generator is UniGLTF-1.28, with no license field. License: MIT. Notice: see Credit lines.
- `game/addons/cogito/Assets/Models/just_a_screw/just_a_screw_meshonly.tres` and `scene.bin`. Source: the credits page, "Just a screw" by XialiMu.Bell (https://skfb.ly/6XVNT), "used under CC Attribution 4.0" (http://creativecommons.org/licenses/by/4.0/). The Sketchfab page that link opens, https://sketchfab.com/3d-models/just-a-screw-407a4e705558487abc450a8eb05fea01, says "License: CC Attribution" and links the same CC BY 4.0 deed. Author: XialiMu.Bell. License: CC BY 4.0. See Credit lines.
- `game/addons/cogito/Assets/VFX/` (scenes, materials, and PNG textures, including Impacts). Source: the credits page's MIT line. The page does not name this folder. License: MIT. Notice: see Credit lines.
- `game/addons/quick_audio/`. Source: `plugin.cfg` (Bryce Dixon), `LICENSE`, and the copyright comment in `Audio.gd`. The credits page names QuickAudio by Bryce Dixon. License: MIT, copyright 2023 Bryce "BtheDestroyer" Dixon. The LICENSE file is in the folder. See Credit lines.
- `game/addons/input_helper/`. Source: `plugin.cfg` (Nathan Hoad) and `LICENSE`. The credits page names InputHelper by Nathan Hoad. License: MIT, copyright 2022-present Nathan Hoad. The LICENSE file is in the folder. See Credit lines.
- `game/addons/godot_state_charts/`. Source: `plugin.cfg` (Jan Thomä & Contributors) and `LICENSE`. The credits page names "Godot State Charts by derkork + contributors". License: MIT, copyright 2023 Jan Thomä. The LICENSE file is in the folder. See Credit lines.

### Credit lines

These licenses ask for a credit or for the copyright notice to stay with the copy.

- Montserrat, SIL Open Font License 1.1. Condition 2: a copy bundled with software must contain the copyright notice and the license. Notice in the bundled font: "Copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat)". Designer: Julieta Ulanovsky. License: SIL Open Font License, Version 1.1, http://scripts.sil.org/OFL. The folder now includes `OFL.txt` (the 2011 copyright line and the full OFL 1.1 text) next to the fonts, as well as the short statement in the font name table.
- Freesound's plain-text line for each CC BY sound. The CC BY 4.0 deed (https://creativecommons.org/licenses/by/4.0/) requires appropriate credit, a link to the license, and a note if changes were made. CC BY 3.0 (http://creativecommons.org/licenses/by/3.0/) also requires the title. Freesound supplies these lines:
  - `Alarm Siren.wav by mirkosukovic -- https://freesound.org/s/435666/ -- License: Attribution 4.0`
  - `Running Water by Poyekhali -- https://freesound.org/s/241842/ -- License: Attribution 3.0`
  - `Underwater Deep Water Loop by Department64 -- https://freesound.org/s/651743/ -- License: Attribution 4.0`
- Fireplace Sound loop by PagDev, https://opengameart.org/content/fireplace-sound-loop, CC0. Not required by the license; credited because the author asked (2026-10-27) and the page says credit "is always appreciated".
- "Just a screw" by XialiMu.Bell, https://skfb.ly/6XVNT, CC BY 4.0, http://creativecommons.org/licenses/by/4.0/. The deed also asks for a note if the model was changed. Whether this mesh differs from the Sketchfab file was not checked.
- MIT. The license says the copyright notice and the permission notice must be included in all copies or substantial portions.
  - `game/addons/quick_audio/LICENSE`: Copyright (c) 2023 Bryce "BtheDestroyer" Dixon.
  - `game/addons/input_helper/LICENSE`: Copyright (c) 2022-present Nathan Hoad.
  - `game/addons/godot_state_charts/LICENSE`: Copyright (c) 2023 Jan Thomä.
  - Assets held under the MIT line (the gamepad icon sheet, the HourOfOblivion barks, `vending_machine_sfx.ogg`, `shelf_base.glb`, `shelf_drawer.glb`, `ladder.glb`, `pistol.glb`, `target.glb`, and `game/addons/cogito/Assets/VFX/`): `game/LICENSE` says Copyright (c) 2023 Phazorknight and includes the permission notice. The credits page's MIT block says Copyright © 2026 Phazorknight + Contributors.

### Replaced assets

The five files with unknown or non-commercial licenses (the CC BY-NC fireplace sound, the two sliding-door sounds and the two Freepik flags) were replaced or cut on `playtest-lens` in `1a381f1`. See the entries above.

## Telemetry prior work (read, not used)

Research only, 2026-10-28: no code, dependency or asset came from these. They informed the shape of our own add-on and this list is the credit for that.

- etodd/playtest-telemetry-godot (MIT): uploads to a server, so not reusable here; read for event naming.
- GhostTrail (MIT): 2D and reloads the editor on stop; read for the reload idea.
- OpenTelemetry's Logs Data Model and the Perfetto Chrome JSON trace format: read as schema references.
- Godot's `EditorNode3DGizmoPlugin`: the documented path for drawing in the editor viewport, noted for a later editor view.

## Prepared before building started

- This repo's planning notes, agent rules and skills (`PLAN.md`, `AGENTS.md`, `CLAUDE.md`, `STATUS.md`, `README.md`, `docs/`, `.claude/skills/`), drafted on 2026-10-26 around the kickoff. The rules, the review loop and the skills adapt working rules the author uses on his other projects: process only, no code or content from them. No code.

Building started after the kickoff on 2026-10-26 at 12:00 ET.

## Built during the hackathon

Everything else: the analyzer, the checking pass, the report page, the logging add-on and its COGITO adapter, the open-weights mode, and the commits on the COGITO fork's `playtest-lens` branch. The git history shows when.

### The commits on `playtest-lens`

On top of upstream's `676be6d`, in order:

- `de772aa` "Open in Godot 4.7.2": the Godot 4.7.2 editor's own rewrite of the 4.6 project, no content changes. `project.godot` `config/features` from `4.6` to `4.7`, and three new default keys in each of 260 `.import` files.
- `33ad57c` "Add the Playtest Lens logging add-on, general part": `addons/playtest_lens/` (a passive logger autoload and its headless test), and in `project.godot` the autoload line and the `playtest_lens/player_path` setting.
- `48f8550` "Add the COGITO adapter to the Playtest Lens logger": `addons/playtest_lens_cogito/` (an autoload on COGITO's signals and its headless test), a public `log_event` in the logger, and in `project.godot` the adapter's autoload line and `playtest_lens/player_path="Player"`.
- `9520a99` "Add the start flash and beep to the Playtest Lens logger": `addons/playtest_lens/start_flash.gd` (a white window for 0.25 s and a 1000 Hz beep generated in code, logged as `start_flash`) and its tests.
- `cbfb616` "Flash and beep at New Game and at each level load": `start_flash.gd` renamed to `addons/playtest_lens/sync_flash.gd`, now flashing on request and logged as `sync_flash` with a `reason`; the logger flashes when a scene with the player loads, the COGITO adapter when the main menu's New Game is pressed; their headless tests.
- `1be0ed4` "Log the player's death, and a scripted session test": a `death` line from the COGITO adapter when the player's health attribute emits `death`, and `addons/playtest_lens_cogito/tests/test_session.gd`, a headless Lobby session (New Game, out and back, 40 s still, a death, a retry) whose log is the analyzer's test fixture.
- `1a381f1` "Replace the fire and sliding-door sounds, cut the flag icons": the five files listed under "Replaced assets" removed; `pagdev_fireplace_loop.ogg` added; `CogitoProperties.tscn`, `sliding_door.tscn`, `language_select.gd` and `OptionsTabMenu.tscn` point at the new sounds or drop the flags.
- `708528e` "Add the UID files Godot 4.7 wrote for the Playtest Lens scripts": nine `.gd.uid` files under `addons/playtest_lens*`.
- `5d585f9` "Log where the player looks; keep the log free of paths that name a person": `yaw` and `pitch` from the camera on each `position` line, `log_path` in its `user://` form, and the scripted session looking around for 20 s of its stand.
- `7ad0f20` "Trim the sliding door's open sound to 0.4 s with a fade-out": `addons/cogito/Assets/Audio/sliding_door_open.ogg`, the first 0.4 s of Kenney's `stoneDrag4.ogg` (CC0) with a 0.1 s fade-out, used as `sliding_door.tscn`'s `open_sound`.
- `b0b3647` "Unhook telemetry volumes after the old level is already freed": the logger no longer keeps the volume node. COGITO frees the old scene before the next one is current, and reading the stored node aborted the load.

## Development tools (not part of the product)

- DeepSeek V4.1 Flash 1017 (DeepSeek, open weights) wrote part of the early code, served on Modal as a Shared Endpoint and driven by `tools/run-modal-agent.sh`. Modal's agent skill (`modal skills install --claude`) is installed locally and git-ignored. The product itself calls only Meta models (Muse Spark, Voice Transcribe, and Muse Spark Open for the open-weights mode).
- Grok 4.7 (xAI, through Cursor) reviews code and built the Godot side and tools. The author's Grok bot, on its own machine and briefed by him, wrote some of the fork's Godot tool commits (`grok-bot` in the fork's history). Claude Sonnet 5.5 orchestrated until 2026-10-31; since then Claude Opus 5.5 orchestrates and writes the code, Claude Fable 5.1 designed the report page, and Claude Sonnet 5.5 reviews the page. Every commit names its author models in a `Co-Authored-By:` trailer.

The top-down maps in `report/maps/` and the fork's `maps/` are renders of COGITO's demo scenes (Lobby and Laboratory) made by our map tool (`godot/tools/map_export.gd` in this repo since 2026-10-31; first written in the fork's `tools/`), so their geometry is COGITO's (MIT, credited above); the tool and the pictures' framing are ours.
