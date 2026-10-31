# Godot side

- `addons/playtest_lens/`: the Playtest Lens add-on, a passive session logger for any Godot 4 game. Its README says how to install it.
- `tools/map_export.gd`: draws a top-down map of each floor of a level, with the JSON that maps world positions to pixels. Run it against your project: `godot --path <your project> --script <this repo>/godot/tools/map_export.gd -- <res://level.tscn> <out_prefix> [y_cutoff] [--floor-min=Y] [--box=min_x,max_x,min_z,max_z] [--hide=node/path,...]`. It needs a window, not `--headless`.
- `project.godot`: a minimal project that holds the add-on, so its tests run outside any game: `godot --headless --path godot res://addons/playtest_lens/tests/test_logger.tscn` (also `test_sync_flash`, `test_telemetry_volume`).
