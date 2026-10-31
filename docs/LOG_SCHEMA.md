# Log schema, version 1

One JSON object per line, written by the Playtest Lens logger (`game/addons/playtest_lens/logger.gd`). Times are seconds from session start, on one clock: the same clock the `sync_flash` line marks, so log time maps to video time through the first flash.

Every line has `t` (number) and `event` (string). While the player is inside a telemetry volume, every line also carries that volume's `zone` and `puzzle`; `zone_enter` and `zone_exit` are separate lines that name their own volume.

| Event | Fields | Meaning |
|---|---|---|
| `session_start` | `schema` (1), `session_id`, `wall_time`, `godot_version`, `game_name`, `game_version`, `os`, `renderer`, `log_path` | First line. A `schema` newer than 1 is rejected by the analyzer, not read. |
| `session_end` | `reason` (`quit`) | Last line. May be missing after a crash. |
| `sync_flash` | `reason`, `duration_s`, `beep_hz`, sometimes `scene` | The white flash and beep that line the log up with the video. |
| `scene` | `scene` | The current scene changed. |
| `position` | `x`, `y`, `z`, sometimes `yaw`, `pitch` | Player position every 0.5 s, with view direction when a camera is found. |
| `input` | `action`, `pressed` | An input action went down or up. Listening only. |
| `pause` / `resume` | none | The tree paused or resumed. Paused time is not idle time: the analyzer closes stretches at these lines and ignores positions between them. |
| `perf` | `fps`, `frame_ms` | Once a second. A hitch marker for the analyst, not a candidate source. |
| `marker` | none | The player pressed F9 to mark a moment. Listening only. |
| `zone_enter` / `zone_exit` | `zone`, `puzzle` | The player entered or left a telemetry volume. |
| `death` | none | From the COGITO adapter: the player died. |
| adapter events | varies | Pickup, door, lock, keypad and quest lines from the COGITO adapter. Unknown events are ignored by the analyzer. |

Consumers: `analyzer/log_candidates.py` (deaths, retries, idle, looking around, backtracks), `analyzer/beats.py` (zone intervals bound Attempts), `analyzer/check.py` (the log slice inside each checked clip), and `analyzer/spatial.py` (the route, with the floor from `position` `y`; heat; F9 markers; door, pickup, quest, lock, pause and resume lines as the report's game events).
