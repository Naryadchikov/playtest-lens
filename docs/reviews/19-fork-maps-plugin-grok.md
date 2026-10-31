Reviewer: Grok 4.7 xhigh through Cursor, fork commits 1bd0281, b4709dc.

NOT PASS. 1 blocking finding.

Headless exits, Godot 4.7.2: test_logger 0, test_sync_flash 0, test_telemetry_volume 0, test_adapter 0, test_new_game 0, test_session 1 then 0 on rerun. The first session miss is outside these commits: the first position sample was 1.61 m from the stand, and the test allows 1.5 m (`game/addons/playtest_lens_cogito/tests/test_session.gd:315`). `logger.gd` and that test are unchanged here. Positional cutoff still sets `y_cutoff` (3.5 on a small scene). `--floor-min` and `--box` in either order write the same PNG and JSON. On that scene, player (2, 3) with `--box=-10,10,-10,10` maps to px 1228.8, py 1331.2 of 2048 x 2048, which is the JSON formula. Lobby with no options matches the old tool's PNG byte for byte (39026 bytes, sha256 fbaa0e08ab64d3e2), and that PNG matches `report/maps/lobby.png`. Lobby upper with cutoff 4.5, `--floor-min=2.4`, `--box=-9,10,-25,18` matches `report/maps/lobby_upper.json` byte for byte, and the player start maps to px 573.0, py 336.6 of 905 x 2048. A missing `--hide` node exits 2 with `--hide: no node ...`. No key, token, recording, or private file in the diff. No em dashes. `map_export.gd` only draws a copy with scripts stripped. `plugin.gd` is editor-only.

Blocking:

1. `game/tools/map_export.gd:42`. A `--box` that splits into four parts is accepted even when the parts are not ordered numbers, and the tool exits 0 and writes a map. `--box=a,b,c,d` becomes world box 0,0,0,0, a 0 x 0 image, and `player_start` nan. The message is Godot's camera `set_size` error, and there is no `--box` error. `--box=10,-9,-5,5` exits 0 and writes `px_width` -3891. `--box=1,2,3` does fail: exit 2, `--box needs min_x,max_x,min_z,max_z`.

Nits:

1. `game/tools/map_export.gd:137`. With no options the PNG matches the old tool. The JSON adds `"y_floor_min": null`, so the files differ (Lobby JSON 425 bytes from the old tool, 447 from the new one). The committed Lobby JSON is the new form.
2. `game/tools/map_export.gd:30`. The usage line printed for too few arguments lists only `[y_cutoff]`.
3. `game/addons/playtest_lens/README.md:141`. The table says the analyzer knows `keypad` (`README.md:147`). `analyzer/findings.py:14` and `analyzer/spatial.py:82` omit it, so the report's event list drops keypad lines. The check slice still includes the raw line. The death and retry sentence matches `analyzer/log_candidates.py`. The example lines match `logger.gd` and `docs/LOG_SCHEMA.md` (a real `session_start` from the logger test uses `godot_version` `4.7.2-stable (official)`). `log_event(event_name, fields)` matches `logger.gd:211`.

What I did not check:

- Enable and Disable were not clicked in Project Settings. On a copy, `add_autoload_singleton` then `remove_autoload_singleton` left the autoload unset, and `ProjectSettings.save()` wrote no `playtest_lens/player_path` (editor exit 0). The real `_enable_plugin` and `_disable_plugin` only call those two methods. `plugin.gd` is not in `editor_plugins`, is not an autoload, and nothing preloads it. No export was built.
- Upper PNG bytes differ from `report/maps/lobby_upper.png` (19465 vs 19715). The four `--hide` paths are not in the JSON, so that rerun omitted them.
- Height-gradient pixels were not sampled. The no-option PNG matches the old shader. A `--floor-min` render of one box differs from the same box without it (17107 vs 17147 bytes).
- The GitHub links were not fetched. No network. They are expected to work once those repos are public.
- The Linux user-data path was not checked.
- `game/project.godot` was left as it was. These runs did not change it.
