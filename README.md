# Playtest Lens

Watching a playtest takes as long as the playtest. A 20-minute session is 20 minutes of video, so small teams skip it or skim it, and the moment a player got lost is never seen by the person who built the room.

Playtest Lens watches it for you. Meta's Muse Spark watches the recording and listens to the player thinking out loud, a second Spark pass has to check every moment against its clip and the game's own event log, and you get one page: where the player was confused, stuck or surprised, on the level's map, with the clip and the player's own words.

Muse Spark 1.2 takes each 2-minute window of the recording as video with its sound in one request, so the finding step needs no frame sampling and no separate speech model, and a 21-minute playtest costs about $0.18. On a playtest nothing was tuned on, it found the places where the developer saw the player slowed, flagged a possible bug, and rated the friction higher than he did.

**[Open the live demo](https://naryadchikov.github.io/playtest-lens-demo/)**: two real playtests of the same level, no install.

![The report: the top problem, its clip with the player's words, the map with the route walked](https://naryadchikov.github.io/playtest-lens-demo/report.gif)

<!-- Demo video: the link goes here once it is uploaded. -->

## What you get

One page per playtest, in two modes.

- **Read** is a page to scroll. A one-line verdict, the top problems beside the level's map, then every moment in order under the room or puzzle it happened in, each with a still frame, and last the moments the check threw away, each with its reason.
- **Watch** opens from any moment. The clip fills most of the screen with the player's words as its headline, what happened and the likely cause under it. Beside it, the map shows where the player is, where they walked in the last 30 seconds and the last thing the game logged. Play the session walks the route on the map and stops at each moment the level did not plan for.

Each moment says whether the friction was **by design** (learning the controls, exploring, a planned surprise) or **unplanned** (stuck, or blocked with no way forward), so a designer knows what to fix first.

## How it works

1. **Record.** The tester plays your Godot build and records the screen with the microphone on, with OBS or any screen recorder. The [Playtest Lens add-on](godot/addons/playtest_lens/) writes an event log as they play: inputs, position and view, rooms and puzzles entered, doors, pickups, quest steps. It flashes white and beeps at each level load (and the COGITO adapter also at New Game), so the video and the log line up to the frame.
2. **Find.** Muse Spark watches the video with its sound in 2-minute windows and lists moments worth a look, each with a time and a reason.
3. **Check.** For each moment, a second Spark call gets the 20-second clip, the player's words and that slice of the event log, and must keep or drop it with evidence: what happened, the friction, whether the player got past it, and the likely cause in the level. Muse Voice Transcribe writes down what the player said, and a quote reaches the page only when it is in that transcript. Dropped moments are listed with the reason, not hidden.
4. **Report.** The findings file is the single truth: it holds every moment, the route, the rooms and the summary, and the page only draws it. One command runs it all, and every model reply is cached, so a rerun costs nothing.

## On three real playtests

Three playtests of the Lobby level of the COGITO demo, each player thinking out loud: two testers who had never seen it, and the developer's own run (in the numbers only, not on the demo site).

| | Player 1 | Player 2 (held out) | The developer |
|---|---|---|---|
| Length | 21:21 | 6:04 | 8:32 |
| Spark: kept, dropped | 24, 4 | 10, 0 | 8, 8 |
| Open: kept, dropped | 32, 15 | 14, 3 | 13, 5 |
| Cost per session, Spark | about $0.18 | about $0.06 | about $0.09 |
| Cost per session, Open | about $2.30 | about $0.70 | about $0.90 |

Spark is Muse Spark 1.2 (contributor) through the Meta Model API; Open is Muse Spark Open on Baseten. The costs include Voice Transcribe.

**Player 1** kept coming back to the Archive's code lock, three attempts in all. The Spark page puts it first, "Archive, Code Lock", with the moment she says "I still still don't know what is the code", and shows that she got into the Archive through the toilet duct instead.

**Player 2 was held out.** Nothing was tuned on this session. The developer watched him play and wrote notes blind, then compared them with the page:

- **Found:** the places where he was slowed. The Archive code door (he never found the code), the CEO Office door (he got in with the key instead), and the toilet duct he used to reach the Archive.
- **A bonus:** a freeze when he shot the Archive door, logged as a suspected bug. The developer thinks it can be a real one.
- **Overrated:** the friction. The developer saw no one stuck; the page calls three moments blocked, the code door among them, which the developer counts as a problem but not a blocker.
- **Missed, and can't see:** that he never opened a drawer, so he never found the lockpicks or the code note. Nothing in the video or the log shows a drawer that was never tried.

The developer also judged the cards that changed between the last two versions of the check prompt, on Player 1's session and his own, in both modes: he agreed with the final prompt on 17 of 21.

## Use of Meta's models

- **Muse Spark 1.2 (contributor)** watches the whole session with its sound and finds the candidates, then checks each one against its clip and the log. Two passes of the same model with different jobs: the first one proposes, the second one has to prove each claim with the clip, the player's words and the log, or drop it.
- **Muse Voice Transcribe** writes down each clip's speech. The check reads the player's words as text, and the page shows only quotes the transcript holds.
- **Muse Spark Open** on Baseten runs the same pipeline as a separate open-weights mode (below).

## Open-weights mode

The same pipeline runs on Muse Spark Open (`meta-models/muse-spark-open-1026`) on Baseten. Each request sends the clip as video and its audio as a separate track; quotes are still checked against Voice Transcribe. Open finds more and keeps more, and costs more: of the moments Spark kept, Open also kept 20 of 24, 9 of 10 and 7 of 8 within 15 seconds. Spark's pages were easier to read; Open's catch more small confusions.

## Run it

Python 3.13 with `requirements.txt` in `.venv`, and ffmpeg. Keys live in the macOS Keychain; the two scripts read them for one process only.

```
tools/run-analyzer.sh analyzer/analyze.py <recording> --log <session.jsonl>
tools/run-baseten.sh  analyzer/analyze.py <recording> --log <session.jsonl> --model meta-models/muse-spark-open-1026
```

It finds the start flash, runs the candidate pass and the check, and writes the findings file and the page to `runs/check/` (`--out-dir` to change it). Every model reply is cached by a hash of its request, so a rerun on the same input costs nothing, and every call is logged with its tokens and cost. The offline tests run with `.venv/bin/python -m pytest -q` and make no model call.

To redo only the map data on an existing findings file, with no model call: `.venv/bin/python -m analyzer.spatial <findings.json> --log <session.jsonl> --video-flash-s <seconds>`.

## The Godot add-on

[`godot/addons/playtest_lens`](godot/addons/playtest_lens/) is a standalone Godot 4 plugin: copy it into your game, enable it, set the player path. It only listens and writes; it never changes gameplay, timing or input, and it logs nothing that names a person or a machine. Telemetry volumes let a designer name rooms and puzzles, and the page groups moments by them. [`godot/tools/map_export.gd`](godot/tools/map_export.gd) draws the top-down map of each floor of a level. `godot/` is a minimal project that runs the add-on's tests outside any game. The COGITO adapter (doors, keypads, pickups, quest steps) lives in the test game's fork, [cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens/tree/playtest-lens/addons/playtest_lens_cogito), with a copy of the add-on for the demo build.

## How it was built

Solo, by a level designer, during the hackathon, with coding agents in T3 Code. Claude Opus 5.5 planned and wrote most of the code, Claude Fable 5.1 designed the report page, Grok 4.7 through Cursor reviewed the code, and Claude Sonnet 5.5 reviewed the page's UX. Muse Code helped in the first days. Each task's brief and what came back are in [docs/tasks/](docs/tasks/), each review in [docs/reviews/](docs/reviews/), and each commit names its author model in its trailers.

## Built with

- Meta: Muse Spark 1.2 (contributor), Muse Voice Transcribe, Muse Spark Open on Baseten.
- Test game: the COGITO demo by Phazorknight (MIT), from codeberg.org/Phazorknight/Cogito at 676be6d, in a fork, [cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens). Prior work and asset licenses: [docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).
- Godot 4.7.2, Python 3.13, ffmpeg.

## License

MIT. See [LICENSE](LICENSE).
