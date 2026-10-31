# Playtest Lens

Watching playtest recordings takes hours, so small teams skip it or skim it, and the moment a player got lost is never seen by the person who built the room.

Playtest Lens watches the recording for you. Meta's Muse Spark watches the video and listens to the player thinking out loud, a second Spark pass checks every moment against its clip and the game's own event log, and you get one page: where the player was confused, stuck or surprised, on the level's map, floor by floor, with the clip and the player's words beside it.

<!-- GIF: the report page playing. Captured from a session whose player allowed public use. -->

## How it works

1. **Record.** The tester plays your Godot build and records the screen with their microphone on (Xbox Game Bar, OBS, or a stream). The [Playtest Lens add-on](https://github.com/Naryadchikov/cogito-playtest-lens/tree/playtest-lens/addons/playtest_lens) writes an event log as they play: inputs, position and view, rooms entered, doors, pickups, quest steps. It flashes white and beeps at New Game, so the video and the log line up to the frame.
2. **Find.** Muse Spark watches the video with its sound in 2-minute windows and lists moments worth a look, each with a time and a reason.
3. **Check.** A second Spark call gets each moment's 20-second clip and that slice of the event log, and must keep or drop it with evidence. Muse Voice Transcribe writes down what the player said in the clip, and a quote reaches the page only when it is in that transcript. Dropped moments are listed with the reason, not hidden.
4. **Report.** One page per session: the worst places first, both floors of the level with the route walked on each, every kept moment with its clip, the player's words, what the game was doing and the check's note, and the dropped candidates. Play runs the session on the map; scrolling to a moment lights it on the map, and playing its clip moves the player's dot.

## On a real session

A 21-minute first playthrough of the COGITO demo's Lobby by a player who had never seen it:

| | Normal mode: Muse Spark 1.2 (contributor) | Open-weights mode: Muse Spark Open on Baseten |
|---|---|---|
| Candidates found | 29 | 47 |
| Kept by the check | 24 | 33 |
| Dropped, with a reason | 5 | 14 |
| Model cost for the session | $0.10 | $2.09 |

Voice Transcribe cost $0.16 across both runs. 21 of the 24 moments normal mode kept also appear in open mode within 15 seconds.

<!-- The developer's check of the 24 cards goes here: right, wrong, unsure. Not blind: he read the report first. -->

## Open-weights mode

The same pipeline runs on Muse Spark Open (`meta-models/muse-spark-open-1026`), hosted on Baseten. Each request sends the clip as video and its audio as a separate track; quotes are still checked against Voice Transcribe. Open mode finds more and keeps more; normal mode was easier to read on this session and missed nothing the developer cared about.

## Run it

Python 3.13 with `requirements.txt` in `.venv`, and ffmpeg. Keys live in the macOS Keychain; the two scripts read them for one process only.

```
tools/run-analyzer.sh analyzer/analyze.py <recording.mkv> --log <session.jsonl>
tools/run-baseten.sh  analyzer/analyze.py <recording.mkv> --log <session.jsonl> --model meta-models/muse-spark-open-1026
```

It finds the start flash, runs the candidate pass and the check, and writes the findings file and the page to `runs/check/`. Every model reply is cached by a hash of its request, so a rerun on the same input costs nothing, and every call is logged with its tokens and cost.

To redo only the map data on an existing findings file, with no model call: `.venv/bin/python -m analyzer.spatial <findings.json> --log <session.jsonl> --video-flash-s <seconds>`.

## The Godot add-on

`addons/playtest_lens` in [cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens/tree/playtest-lens/addons/playtest_lens) is a standalone Godot 4 plugin: copy it into your game, enable it, set the player path. It only listens and writes; it never changes gameplay, timing or input, and it logs nothing that names a person or a machine. Telemetry volumes let a designer name rooms and puzzles, and the report groups moments by them. `tools/map_export.gd` in the same fork draws the top-down map of each floor.

## Built with

- Meta: Muse Spark 1.2 (contributor), Muse Voice Transcribe, Muse Spark Open on Baseten. Muse Code helped build the first days.
- Test game: the COGITO demo by Phazorknight (MIT), from codeberg.org/Phazorknight/Cogito at 676be6d, in Sasha's fork [cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens). Prior work and asset licenses: [docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).
- Godot 4.7.2, Python 3.13, ffmpeg.
- Built with coding agents from T3 Code: Claude Code, Grok through Cursor, Muse Code, and DeepSeek, GLM and Kimi on Modal. Which agent built what is in [docs/tasks/](docs/tasks/) and in each commit's trailers.

## License

MIT. See [LICENSE](LICENSE).
