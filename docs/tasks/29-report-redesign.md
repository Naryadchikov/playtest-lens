# 29: Report redesign, three mockups, then one build

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Base commit: `b36e564` on `main`.

## Why

Sasha, T3 Code chat, 2026-10-31: "better to polish the report, dont hesitate to redesign it completely if you think it is better, I think bigger map with 2 levels is the better thing, maybe more dynamic events on the page and would be nice if you see both the map and the clip with the bit along side somehow, dont hesitate to run couple of ideas and pick the best."

His tester's session is all in the COGITO Lobby, on two floors (ground, and an upper floor at about y 3.5 that holds about a quarter of her time). Today's page draws both floors on one plan, so the route is a tangle, and the clip sits far from the map.

## Step 1: three mockups (Claude Opus 5.5 subagents, in parallel)

Each designer makes one standalone HTML page for one direction, on the real session data. The orchestrator (Claude Opus 5.5) picks one, or a mix, and builds it in `report/render.py` with the analyzer supplying any new data.

### Shared inputs (all in `runs/design/`, git-ignored, a tester's private session: never copy any of it into the repo)

- `data-spark.js` sets `window.DATA` (Contributor Spark 1.2, the page Sasha shows). `data-open.js` is the same shape for Muse Spark Open.
  - `session`, `summary` (verdict sentence, lost_s, counts, kept, dropped).
  - `findings`: every candidate. `check.verdict` is `keep` or `drop`; kept ones have `rank`, `time_s`, `end_s`, `kind`, `summary`, `quote`, `game_state`, `check.note`, `check.friction` (`learning`, `stuck`, `blocked`), `check.resolved`, `beat` (area, puzzle, puzzle_number, attempt, attempt_start_s, attempt_end_s), `at` (`x`, `z`, `floor` 0 or 1), and `clip` (`path` relative to `runs/design/`, `start_s`, `end_s` in session video seconds; a clip is about 20 s, 1280x720 H.264).
  - `route.points_t_x_z_floor`: `[t, x, z, floor]` about once a second, video seconds, world metres. `route.heat`: hot spots `{x, z, r_m, seconds}` (no floor yet).
  - `maps.meta`: `px = (x - world_min_x) / (world_max_x - world_min_x) * px_width`, `py = (z - world_min_z) / (world_max_z - world_min_z) * px_height`, 1334 x 2048 px, z grows downward. Both floors share this mapping. `maps.floors[0].image` is `floor0.png` (ground), `[1]` is `floor1.png` (upper floor; the black middle is the open atrium, thin lines are ground walls below).
  - `zones`: room visits `{zone, puzzle, start_s, end_s}` from the game's telemetry volumes.
  - `game_events`: `{t, kind, label}` for doors, pickups, quest steps, unlocks, pause and resume. Labels come from game node names and are rough.
- The page today: `runs/check/lobby-player-1-report.html` (render it from `report/render.py`; its wording is in `LABELS` there). Design tokens: `docs/design/DESIGN_NOTES.md`.

### What every mockup must do

- Two floors, bigger than today's map, both readable at once on a 1440 x 900 screen and on 1920 x 1080. The route on each floor is only the part walked on that floor.
- The map and the clip and the moment ("the bit") visible together. When a clip plays, a dot on the map follows the player: map time = `clip.start_s + video.currentTime`, moved to the route point at that time, on that point's floor.
- Some motion that answers time: a Play control for the whole session, moments and game events appearing as time passes. Keep Sasha's earlier decisions: the heat map is its own view and turns the timeline view off ("heat map should be turning off the timeline view, and just be the heat map"); the map opens on the whole route; trail windows of 10, 15, 30 and 60 s exist today and may stay.
- The full list of kept moments is still on the page, grouped Area, Puzzle, Attempt (Sasha's hierarchy, DECISIONS.md 2026-10-28), and the dropped candidates with their reasons. Dropped candidates matter to the judges: they show the check at work.
- Kind is never color alone: stuck square, confused circle, surprised diamond, suspected bug triangle.
- Words: reuse `LABELS` wording where it fits. Any new visible word is a proposal: list them in your report. "by design" is a proposal Sasha may change. English. No em dashes and no spaced en dashes anywhere.
- Light and dark (`prefers-color-scheme`), `prefers-reduced-motion`, keyboard reachable, escaped strings.
- Plain HTML, CSS and JavaScript in one file, no libraries, no network. The final page computes nothing that is a finding, a time, a position or a count; in the mockup your script may derive things, but list each one so the analyzer can supply it.

### Rules for designers

- Write only your own file: `runs/design/mockup-<letter>.html`, plus screenshots under `/tmp/<letter>-shots/`. Do not edit anything else in the repo. Do not commit.
- Do not call any t3-code tools. Never run rm. No model calls, no network, no Keychain.
- Videos do not decode in headless Firefox on this Mac (a decoder error, not the files). Wire the video logic anyway; Chrome is not installed yet.
- Screenshots: `/Applications/Firefox.app/Contents/MacOS/firefox --headless --no-remote --profile <your empty dir under /tmp> --window-size=1440,900 --screenshot <out.png> file://<page>`. For dark or light put `user_pref("layout.css.prefers-color-scheme.content-override", 0);` (dark) or `1` (light) in that profile's `user.js`. Use a different empty profile dir for each run in parallel with other designers. Headless screenshots cannot click or scroll: add a URL hash or query your page reads (for example `#t=600` or `#moment=4`) so you can capture states.

### Report (short)

The file path; screenshot paths (1440 x 900 dark, 1440 x 900 light, one at a selected moment); what your script derives that the analyzer would have to supply; new words; what you could not check.

## Step 2: the build

Filled in after the pick: the chosen direction, the analyzer fields, the tests, the review.
