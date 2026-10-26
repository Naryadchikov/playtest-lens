# What existed before the hackathon

The hackathon's rule: what's presented must be built during the event, and what existed before must be clearly identified.

## Third-party

- **COGITO** by Phazorknight (MIT), the immersive-sim template whose demo is the test game. Origin: codeberg.org/Phazorknight/Cogito at 676be6d (MIT). Sasha's copy, [github.com/Naryadchikov/cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens), keeps upstream's `main` at that commit, unchanged, with its full history. Our changes are only the commits on its `playtest-lens` branch, listed below. It's the submodule at `game/`.
- **Godot 4.7.2**, **Python**, **ffmpeg**, and any library listed in the analyzer's requirements file.
- Demo asset credits: listed here once each asset's license is checked.
- Tools used to build it, not part of the submission: T3 Code, Claude Code, Muse Code and Cursor.

## Demo assets to check

From the COGITO checkout at 676be6d (`game/`). "Unknown" means no file in that checkout states a license. `game/Readme.md` links to https://codeberg.org/Phazorknight/Cogito/wiki/Credits%2C-Contributors%2C-License for credits and license. That page is not in this checkout, so it is not a source below.

- `game/addons/cogito/Assets/Textures/Prototype Textures/` (80 PNG files and `License.txt`). Source: `License.txt` in that folder, Kenney (www.kenney.nl), dated 08-04-2020. License: CC0 (Creative Commons Zero) 1.0. The file asks for a Kenney credit and says it is not mandatory.
- `game/addons/cogito/Assets/Models/Kenney/` (252 `.glb` files: `barrel.glb`, `bag.glb`, `toolPickaxe.glb`, `chest.glb`, plus the Blaster, Furniture, and SpaceInterior packs). Source: the folder name, and the name Kenney under ASSETS in `game/addons/cogito/cogito_credit_list.txt`. `barrel.glb` names generator UniGLTF-2.34.0 and has no license field. No license file in the folder. License: unknown.
- `game/addons/cogito/Assets/Audio/Kenney/` (57 `.ogg` and `.wav` files, including Impacts, VoiceFemale, Footsteps, and UiAudio). Source: the folder name and the same credit-list line. No license file. License: unknown.
- `game/addons/cogito/Assets/Graphics/Crosshair_Kenney/` (6 PNG files). Source: the folder name. License: unknown.
- `game/addons/cogito/Assets/Graphics/InputIcons/InputIconSheet_Kenney_Xbox.png`, `InputIconSheet_Kenney_SteamDeck.png`, `InputIconSheet_Kenney_KeyboardMouse.png`, `InputIconSheet_Kenney_PS.png`. Source: the file names. License: unknown.
- `game/addons/cogito/Assets/Graphics/InputIcons/InputIconSheet_Gamepad.png`. Source: none in the name. It is in the same folder as the Kenney sheets. License: unknown.
- Quaternius is named under ASSETS in `game/addons/cogito/cogito_credit_list.txt` with no path. License: unknown. `game/addons/cogito/Assets/UniversalAnimationLibrary/AnimationLibrary_Godot_Standard.glb` is the only file in that folder. Its glTF generator is Khronos glTF Blender I/O v4.3.47, with no copyright or license field. `game/addons/cogito/PackedScenes/cogito_player_advanced.tscn` embeds a resource named `AnimationLibrary_Godot_Standard_Mannequin`. The checkout does not say that file is Quaternius. License: unknown.
- `game/addons/cogito/Assets/Fonts/Montserrat/` (18 `.ttf` files). Source: the name table of `Montserrat-Regular.ttf`, copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat), designer Julieta Ulanovsky. License, stated in that name table: SIL Open Font License, Version 1.1 (http://scripts.sil.org/OFL). The license text is not a separate file in the folder.
- `game/addons/cogito/Assets/hdris/kloofendal_48d_partly_cloudy_puresky_2k.hdr`. Source: the file name only. No license file or comment. License: unknown.
- Sounds whose names look like freesound uploads. No license file. The file name is the only source text. License: unknown.
  - `game/addons/cogito/Assets/Audio/241842_poyekhali_running-water.ogg`
  - `game/addons/cogito/Assets/Audio/435666__mirkosukovic__alarm-siren.wav`
  - `game/addons/cogito/Assets/Audio/524306_bertsz_flame_ignite.ogg`
  - `game/addons/cogito/Assets/Audio/537275__laughingfish78__dirt-sliding.ogg`
  - `game/addons/cogito/Assets/Audio/641848_newlocknew_fireburn.ogg`
  - `game/addons/cogito/Assets/Audio/651743__department64__underwater-deep-water-loop.ogg`
  - `game/addons/cogito/Assets/Audio/666290_ekrcoaster_water_hot_surface_short.ogg`
  - `game/addons/cogito/Assets/Audio/672201__romankolachnik__water_footsteps_02.wav`
  - `game/addons/cogito/Assets/Audio/squidge316_sliding-door_01.ogg`
  - `game/addons/cogito/Assets/Audio/squidge316_sliding-door_02.ogg` (referenced by `game/addons/cogito/DemoScenes/DemoPrefabs/sliding_door.tscn`)
- `game/addons/cogito/DynamicFootstepSystem/Assets/Audio/` (Dirt, Grass, Stone, Wood, four `.ogg` files each). Source: `game/addons/cogito/DynamicFootstepSystem/Readme.md`, by AC-Arcana. License: CC0, from freesound.org. Dirt: https://freesound.org/people/HenKonen/sounds/682127/ Grass: https://freesound.org/people/HenKonen/sounds/682128/ Stone: https://freesound.org/people/xmike80x/sounds/706207/ Wood: https://freesound.org/people/SpliceSound/sounds/150444/
- `game/addons/cogito/Assets/Audio/HourOfOblivion/` (`bark_chase.ogg`, `bark_endsearch.ogg`, `bark_investigate.ogg`, `bark_search.ogg`). Source: the folder name. HourOfOblivion is under COGITO TEAM in `cogito_credit_list.txt`, not under ASSETS. License: unknown.
- Loose audio with no author in the name. Source: none found. License: unknown. `game/addons/cogito/Assets/Audio/SodaOpen.ogg`, `SodaOpen_EnergyDrinkEffect.ogg`, `Spray.ogg`, `vending_machine_sfx.ogg`.
- `game/addons/cogito/Assets/Graphics/Flags/freepik_flag_de.png` and `freepik_flag_us.png`. Source: the file names (freepik). License: unknown.
- Models with no author string. License: unknown. `game/addons/cogito/Assets/Models/shelf_base.glb`, `shelf_drawer.glb`, `ladder.glb`, `pistol.glb`, `target.glb` (glTF generator UniGLTF-1.28, no license field). `game/addons/cogito/Assets/Models/just_a_screw/just_a_screw_meshonly.tres` and `scene.bin` (no author text).
- `game/addons/cogito/Assets/VFX/` (scenes, materials, and PNG textures, including Impacts). No author comment or license file. License: unknown.
- `game/addons/quick_audio/`. Source: `plugin.cfg` (Bryce Dixon), `LICENSE`, and the copyright comment in `Audio.gd`. Also named in `cogito_credit_list.txt`. License: MIT, copyright 2023 Bryce "BtheDestroyer" Dixon.
- `game/addons/input_helper/`. Source: `plugin.cfg` (Nathan Hoad) and `LICENSE`. Also named in the credit list. License: MIT, copyright 2022-present Nathan Hoad.
- `game/addons/godot_state_charts/`. Source: `plugin.cfg` (Jan Thomä & Contributors) and `LICENSE`. Not named in `cogito_credit_list.txt`. License: MIT, copyright 2023 Jan Thomä.

## Prepared before building started

- This repo's planning notes, agent rules and skills (`PLAN.md`, `AGENTS.md`, `CLAUDE.md`, `DECISIONS.md`, `STATUS.md`, `README.md`, `docs/`, `.claude/skills/`), drafted on 2026-10-26 around the kickoff. The rules, the review loop and the skills adapt working rules Sasha uses on his other projects: process only, no code or content from them. No code.

Building started after the kickoff on 2026-10-26 at 12:00 ET.

## Built during the hackathon

Everything else: the analyzer, the checking pass, the report page, the logging add-on and its COGITO adapter, the open-weights mode, and the commits on the COGITO fork's `playtest-lens` branch. The git history shows when.
