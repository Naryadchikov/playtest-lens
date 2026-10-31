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

## Round 2

Reviewer: Grok 4.7 xhigh through Cursor, commits 0390930, main 5acc6a4.

PASS

Godot 4.7.2.stable.official (ed1daf0bf). Fork 0390930aa2ed03dde524b747b4d51c620136e3f8, main 5acc6a4b4e28091c406bd7018fc8c3af8a47eff8. The round 1 `--box` inputs exit 2, print `--box needs four numbers min_x,max_x,min_z,max_z with min below max`, and write no PNG or JSON: `a,b,c,d` (with a valid cutoff and `--floor-min`), `10,-9,-5,5`, `-9,10,18,-25`, `1,1,0,1`, `0,1,3,3`, `1,2,3`, `1,2,3,4,5`, `1,,3,4`, and `nan,1,0,1`. Positional `y_cutoff` rejects `nope`, `4.5x`, `nan`, and `inf` with `y_cutoff must be a number`. `--floor-min` rejects `abc`, an empty value, `nan`, and `inf` with `--floor-min must be a number`. Zero arguments and one argument exit 2, and the usage line lists `[y_cutoff]`, `--floor-min`, `--box`, and `--hide` (`game/tools/map_export.gd:30`). The upper floor rerun was windowed, not `--headless`: cutoff `4.5`, `--floor-min=2.4`, `--box=-9,10,-25,18`, and the four `hidden_nodes` in `report/maps/lobby_upper.json`. Exit 0. Player start px 573.0, py 336.6 of 905 x 2048. The PNG matches `report/maps/lobby_upper.png` byte for byte (19715 bytes, sha256 4dcbc7c34cf486d169b143e45beb9b1f66b7b251ea00772cf2818474fc930065). The JSON matches `report/maps/lobby_upper.json` byte for byte (621 bytes, sha256 5f6fe87bf8b5253e2acf8191b246c4a46f1d487ba3c86f448a849ba638025ae6). The README at `game/addons/playtest_lens/README.md:141` matches the analyzer: event-list kinds are door, lock, pickup, quest, pause, and resume (`analyzer/findings.py:14`, `analyzer/spatial.py:82`), with no keypad and no death, and the check slice still appends every log line in the window (`analyzer/check.py:177`). Headless exits: test_logger 0, test_sync_flash 0, test_telemetry_volume 0, test_adapter 0, test_new_game 0, test_session 1 then 0 on rerun. The session miss is the pre-existing 1.5 m check (`game/addons/playtest_lens_cogito/tests/test_session.gd:315`): the first position was 1.518 m from the stand. The 0390930 diff is the README line and `tools/map_export.gd`. Main 5acc6a4 adds `hidden_nodes` to the two map JSONs and the round 1 report. The PNGs are not in that commit. No key, token, recording, or private file. No em dash or en dash. `game/project.godot` hash is unchanged (`8305c4cfdc9e7c46b4ec8280ff1e9d5b1b06092eae9fbcababf350fff579c631`). The command-line number parses are the three in `map_export.gd` (lines 38, 46, and 55). `godot/tools/map_export.gd` and `godot/addons/playtest_lens/README.md` match those fork files byte for byte.

Blocking:

None.

Nits:

1. `game/tools/map_export.gd:57`. Class: `is_valid_float` accepts a token whose `float()` is not finite, and the tool exits 0 and writes a map. `float("1e309")` was already accepted before this commit. Here `is_valid_float("1e309")` is true and `float("1e309")` is inf. `--box=-9,1e309,-25,18` with cutoff 4.5 exits 0 and writes a 92-byte PNG. The JSON has `px_width` 0, `px_height` 0, and `world_max_x` 1e99999. Player start prints px 0.0 py 0.0. There is no `--box` error: `-9 >= inf` is false, so the min-below-max check passes. `--box=1e309,10,-25,18` exits 2, because inf is not below 10. `--floor-min=1e309` (line 50), with cutoff 4.5 and `--box=-9,10,-25,18`, exits 0. Lines 86 and 149 treat a non-finite floor as absent, so the JSON has `"y_floor_min": null` and the PNG is 905 x 2048. Positional `1e309` (line 39), with `--box=-9,10,-25,18`, exits 0. The JSON has `"y_cutoff": 1e99999` and the PNG is 905 x 2048. The same lines are in `godot/tools/map_export.gd`.

What I did not check:

- The ground-floor lobby was not rerendered. 5acc6a4 adds `"hidden_nodes": []` to `report/maps/lobby.json`. The upper-floor rerun is the write path for that field, and its JSON matches the committed file.
- Enable and Disable were not clicked. `plugin.gd` is not in 0390930.
- Height pixels were not sampled apart from the byte compare. The upper PNG matches the committed file, so those pixels match.
- GitHub links were not fetched. No network.
- The Linux user-data path was not checked.
- A box whose minimum overflows (`-1e309`) was not run on its own. The maximum overflow above is the case that was run.
- The minimal project under `godot/` was not launched. Its map tool and add-on README match the fork byte for byte.
- `game/project.godot` was left as it was. These runs did not change its hash.
- An uncommitted edit to `game/addons/playtest_lens/tests/test_logger.gd` showed up during this review (it adds `_ensure_actions`). It is not in 0390930. I left it. test_logger's exit 0 is with that edit on disk. I did not review the edit.

## Orchestrator's follow-up (Claude Opus 5.5, Claude Code in T3 Code)

- Round 2 nit fixed in `godot/tools/map_export.gd` (the tool's source since main `9646a66`): every number must also be finite, so `1e309` in the cutoff, `--floor-min` or `--box` exits 2. The upper map still renders byte for byte the same. The fork's copy of the tool was removed in fork `a9f78ac`.
- The uncommitted `test_logger.gd` edit round 2 saw is `_ensure_actions` (the test adds jump, interact and forward when a game lacks them); committed in fork `a9f78ac` and main `9646a66`, passing in both projects. It goes to the next review round.
