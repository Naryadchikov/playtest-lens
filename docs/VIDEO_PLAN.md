# The 3-minute video: shot list

Sasha records and edits it. His structure, T3 Code chat, 2026-10-31: "I record the 3-minute video from the Spark page: one moment, one drop, the map, then Open beside it. The keypad line is mine: she was stuck on the puzzle, not on progression, because the toilet route let her into the Archive." The demo session is Player 1's, and the held-out session is Player 2's (his answers of 2026-11-01 in DECISIONS.md).

Shot list and timings: proposal by Claude Opus 5.5 (Claude Code in T3 Code), 2026-11-01, for the Read and Watch page. Lines under "Say" are suggestions to rewrite or drop; the keypad line is his and is not drafted here.

What the rules need on screen (docs/PUBLIC_CHECKLIST.md): only work built during the hackathon is presented as ours; COGITO, Godot and the assets are named as prior work; Meta's models are visibly the engine. The rubric: Impact 30%, Use of Meta AI tooling 25%, Technical depth 20%, Demo 25%. Stage one is pass or fail on real use of Meta's models, so name them early.

## Before recording

- Open the pages from the local staging copy (`runs/demo-site/site/`, served as `http://localhost:8000/`; the orchestrator starts it) or, after the green light, from the live site. Browser at 1920 x 1080, dark mode, zoom 100%, no bookmarks bar.
- Player 1's Spark page is `lobby-player-1.html`, her Open page `lobby-player-1-open.html`, Player 2's Spark page `lobby-player-2.html`.
- The clips carry the players' voices: keep the page's sound on for the moment in shot 4.

| Time | Show | Say (suggestion) |
|---|---|---|
| 0:00 to 0:15 | Player 1's raw recording scrubbing fast, the 21:21 length visible | "A 20-minute playtest takes 20 minutes to watch, and most small teams never do." |
| 0:15 to 0:35 | The Godot add-on in the editor: the telemetry volumes in the Lobby; then the white start flash in a recording. A caption: "Test level: the COGITO demo (MIT), prior work" | "A small Godot add-on logs what the player does, and flashes once so the video and the log line up." |
| 0:35 to 0:55 | The pipeline in four boxes: Muse Spark finds, Muse Spark checks with the clip and the log, Voice Transcribe confirms the quote, one page | "Meta's Muse Spark watches and listens. A second Spark pass has to prove each moment with the clip, the player's words and the log, or drop it." |
| 0:55 to 1:10 | Player 1's Spark page, Read: the verdict, the top problems beside the map | "One page: what went wrong, and where." |
| 1:10 to 1:40 | Click "Archive, Code Lock". Watch: the clip with her quote as the headline, the likely cause, the dot moving on the map with its 30 s trail. Next to her 19:17 moment, "I still still don't know what is the code" | His keypad line. |
| 1:40 to 1:52 | Back, scroll to the dropped moments, open one: its reason | "It shows what it threw away, and why." |
| 1:52 to 2:12 | Play the session: the map walks the route, "Up next" on the left, it stops at an unplanned moment. Then the "Time spent" switch on the overview map | "Play walks the session and stops where the level failed the player." |
| 2:12 to 2:32 | The Open page beside the Spark page, two windows at 960 x 1080 | "The same pipeline on Muse Spark Open, the open-weights model, on Baseten." |
| 2:32 to 2:50 | Player 2's page: the code door and the suspected bug. A caption: "Held out: nothing tuned on it" | "On a player it never saw, it found where he was slowed and caught a bug, and it rated his friction too high." (His own words for this line are better.) |
| 2:50 to 3:00 | The README with the one command, the repo URL and the demo URL | "Drop the add-on into your Godot game, record, run one command." |

## Where the video goes

1. Upload to YouTube as public or unlisted (the rules need a link anyone can open, signed out). Title suggestion: "Playtest Lens: an AI playtest analyst for game developers (Meta hackathon)".
2. The link goes into the Cerebral Valley submission form, the README (the comment under the GIF), and the demo site's front page. The orchestrator adds both once he sends the link.
3. A 20 to 30 second cut of shots 1:10 to 1:40 and 1:52 to 2:12 is the X post (Most Viral) and the community vote clip.
