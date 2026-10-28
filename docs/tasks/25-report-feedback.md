# 25: Lobby report feedback, for a plan only

Sasha, Cursor chat, 2026-10-28. This file is the feedback. The plan goes in `docs/tasks/25-report-plan.md`. Do not implement.

## What he saw

The page is `runs/check/cogito-report.html`, from `runs/check/cogito-findings.json`. The recording is `recordings/cogito/cogito.mp4` (512 s, 1920x1080). The log is `recordings/cogito/2026-10-28T20-31-08Z.jsonl` (last t 487 s, no `session_end`). Video flash of New Game is at 25.2 s. The log's first `sync_flash` is `new_game` at t 19.64. The session is the Lobby only. The Laboratory load crashed (fixed later on the fork, `b0b3647`). Spark found 26 moments. The check kept 20 and dropped 11. Cost of that run: $0.07.

His volumes in `game/addons/cogito/DemoScenes/COGITO_3_Lobby.tscn`, as committed (`8049b5d`):

- zone `Archive` (several boxes, puzzle empty)
- zone `CEO Office` (puzzle empty)
- zone `Archive`, puzzle `Code Lock` (the only box with a puzzle line)

There is no volume named "break room". The report's "Archive" is the string he typed.

## His words

The map: "having some timeline or filtering on 2d map will be nice, now it looks a bit too messy and not really readable." "it is almost impossible to follow the route of the player since things are just overlapping, I think having timeline and scroll and see things appear will be great." "I still think we can make it better on 2d side inside the report." Not a Godot editor overlay.

Puzzles: "why we still have things called puzzle 1, etc." "there is only one puzzle essentially in the lobby area, and it is code lock, and I only have one volume with filled puzzle line, so I guess we should stop treating everything as puzzle." Finding the real CEO laptop by looking around the office "could be" another puzzle. He did not mark that volume as a puzzle.

`lobby, Puzzle 1: lobby_door_unlock`: "I would not say it actually as important, it is just part of the world building I guess, closed door, that is it, maybe ok to flag in regards to nice to explain more why it is locked, but not really stuck flag with medium sevirity to my taste."

`Archive, Puzzle 13`: "I think this one should have picked the name of the volume, that is break room, why it is not?"

Missed: "we missed the good moment where I found entry to archive room by openning the vent unscrewing the screw. it should be before this one" (the camera and bear trap).

Wrong: "Player repeatedly tried and failed to open the locked CEO Office door, voicing that the visible key does not allow entry." He "aknowledged that I know that key probably can open the door, and decided to open it myself with the unlock mechanic and the pin, so I solved it, seems that the model havent looked further and cut early."

The lockpick card: "I have managed to do it without a real struggle."

Order: the Archive entry "was correctly identified, so why it is in the end, I think we need to improve on the ordering as well."

## Where the code does this

- The page only renders `findings.json`. Route points are already `[t, x, z]`. Pins use `time_s` and `at`. The whole polyline is drawn at once in `report/render.py` `_render_route`. Pins are numbered by `rank` (`figcaption`: "Pins are numbered by rank").
- Section titles are `_group_title`: it prints `Puzzle {number}: {puzzle}` from `beat.puzzle_number`. `analyzer/beats.py` gives every state a puzzle number, and an empty volume puzzle falls back to the zone name, so an Archive box becomes area Archive and puzzle Archive.
- Card order follows rank and beat, not time. That is why a later-ranked Archive entry sits at the end.

## What this pass may change

A one-off: Opus writes the plan, Sonnet high implements, Grok reviews. Then the project goes back to DeepSeek writing and Grok reviewing. Do not spend the Meta API in the plan or the implementation. A re-check of the video, and the open-weights pass, happen after the review, run by the orchestrator.

Split the plan into:

1. Page and beat changes that can be proven by re-rendering the existing `cogito-findings.json` with no model call. Timeline on the map. Titles that do not call a room a puzzle unless the volume's puzzle line is set. Order.
2. Judgment changes that need a new checker pass: the CEO door was solved on purpose, the lockpick was not a struggle, the vent screw is missing, the crash cards say Unity. Name the prompt or code change, and do not run it.
