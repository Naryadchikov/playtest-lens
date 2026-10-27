# Plan

Agreed with Sasha on 2026-10-26. "Playtest Lens" is a working name.

## In one sentence

You give it playtest recordings (the screen plus the player thinking out loud) and the game's event log. It returns a timeline of where players got confused, stuck or surprised, each moment with its clip, the player's words, what the game was doing, and a note on how it was checked, combined across all players.

**Who it's for:** small teams who run playtests but can't pay someone to watch hours of footage.

**Hackathon track:** Indie Developer, "Build for Your World".

## What we build

1. **Record.** A tester plays the build and records the screen and mic (Xbox Game Bar on Windows, Cmd+Shift+5 on a Mac). The game writes an event log as it runs, and flashes white and beeps when the player presses New Game and at each level load, so the video and the log can be lined up.
2. **Find candidates, two ways.** Muse Spark watches the video and listens to the player in one pass and lists moments with a time and a reason. The event log flags its own signals: deaths, retries, long idle stretches, walking back the way you came.
3. **Check each candidate.** A second Spark call gets a 20-second clip, the player's words and that slice of the event log, and must answer keep or drop, with evidence. Dropped moments are listed, not hidden.
4. **Combine across players**, for example: "3 of 4 players stuck at the lab door, for 2:10 on average."
5. **Report.** One web page: a timeline per session, findings ranked, each with clip, quote, game state and check note, plus the summary across players.
6. **Score.** Compare the findings with Sasha's notes. He watches each recording once, blind, before seeing the report, and marks where the player struggled. The demo shows how many of his notes the tool found, and what else it found.

**Open-weights mode**, only if there's time: the same pipeline on Muse Spark Open (sampled frames plus audio), through Baseten or Modal credits, or locally if it fits.

## The test game

The upstream COGITO demo (codeberg.org/Phazorknight/Cogito at 676be6d, MIT; it moved there from GitHub), in Godot 4.7.2, as a submodule of Sasha's public copy, `cogito-playtest-lens` on GitHub (DECISIONS.md, 2026-10-26). Its `main` is upstream's, unchanged; the `playtest-lens` branch has our few changes:
- "Open in Godot 4.7.2" (`de772aa`): the editor's own rewrite of the 4.6 project, no content changes (DECISIONS.md, 2026-10-26);
- the logging add-on wired in;
- the in-game developer helper documents removed, so testers don't read setup notes.

Check the license of every demo asset and credit what needs credit. Sasha writes the testers' task (10 to 15 minutes).

**The Spark test's recording is a different game:** The Talos Principle 2, recorded by Sasha on the PC with Game Bar (DECISIONS.md, 2026-10-27): "I know COGITO too well to struggle in it." It has no event log. His COGITO session is Thursday's play, and its log is what the idle and walk-back numbers are tuned on.

**The logging add-on** is a general Godot add-on (inputs, scene changes, player position by node path) with a COGITO adapter (pickups, doors, keypads, quest steps). It writes JSON lines with a timestamp, including where the player looks (yaw and pitch, twice a second), and nothing that names a person or a machine (DECISIONS.md, 2026-10-27).

## What we don't build

An AI that plays the game; anything for Unreal; anything from Sasha's other games; a custom game; content generation.

## Who builds what

**Decided** (Sasha's, in chat on 2026-10-26, with Claude's additions; confirmed in DECISIONS.md, 2026-10-26): the split in AGENTS.md, "Who does what", made to spend Muse's plan and the Cursor credits before Claude's usage. Claude Opus orchestrates. Muse Code on Muse Wonder writes most of the code: the analyzer (it may know Meta's current API better than models trained earlier) and the report page. Grok builds the Godot side and the tools. Claude Sonnet reviews. AGENTS.md, "When to switch to more Claude", says when an area moves to Claude. Each task is briefed and recorded in `docs/tasks/`.

## Which Meta models the product uses

**Decided** with two changes (Claude's proposal, 2026-10-26; Sasha's answer in DECISIONS.md, 2026-10-26). The orchestrator checks the current model list and prices before the Spark test and reports the ids.

- **Muse Spark 1.3** finds the candidates: the whole session, video and audio in one pass. It's the cheap model for long inputs ($1.25 in, $4.25 out per million tokens). Spark 1.3 or 1.2: the Spark test picks the one that hears the player better (DECISIONS.md, 2026-10-26, question 9).
- **Muse Wonder** checks each candidate: a 20-second clip, the player's words and the log slice. Short inputs keep its price ($4 in, $20 out) small, and a second model that never sees the first one's reasoning judges the moment on its own. If the Spark test shows Spark checks just as well, the check stays on Spark.
- **Muse Voice Transcribe:** Sasha: "Voice Transcribe stays, used per candidate: transcribe each 20-second clip, so the report's quotes are what I actually said and the check gets my words as text. The times come from Spark and the clip's place in the video." (It returns no word-level times.)
- **Muse Spark Open:** the open-weights mode, through Baseten or Modal. Sasha: "Spark Open: hosted only." The hackathon has a bonus prize for the best build on Meta's open models, but this stays first to cut.
- **Not used for now:** Muse Image, SAM 3.1.

## Tuning and the score

**Decided** (Claude's proposal, 2026-10-26; confirmed in DECISIONS.md, 2026-10-26). Before any tuning, split the sessions: Sasha's own recordings and one tester's are for tuning; the rest are held out. His blind notes on the held-out sessions are read only for the final score, so the score in the demo isn't the tool fitted to its own answer key.

## Machine

Sasha's MacBook Pro (M1 Max, 64 GB), kept awake with `caffeinate -dims` while agents run. Godot 4.7.2 with export templates, so the testers' Windows build is exported from the Mac.

## Days

| Day | Sasha | Agents |
|---|---|---|
| Tue Oct 27 | Read the Spark test result. Go if 7 of 10 flagged moments are real, within about 5 s | Tools check, Muse Code check, repo, the Spark test |
| Wed Oct 28 | Write the testers' task | Fork COGITO, open it in 4.7.2, the logging add-on |
| Thu Oct 29 | Play the build for 20 minutes | Test build; first analysis on Sasha's own recording |
| Fri Oct 30 | Send testers the build, the guide and the consent text | The checking pass; event-log candidates |
| Sat to Sun | Testers record. Sasha makes his blind notes, then reads the first reports | Report page, cross-player summary, score |
| Mon Nov 2 | Tune with real data | Tune; open-weights mode if all else works |
| Tue Nov 3 | Freeze. Record the demo | README, PRIOR_WORK, final checks |
| Wed Nov 4 | Edit the 3-minute video, submit by evening Stockholm time | Final checks |

The deadline is Nov 4, 21:00 ET (Thu Nov 5, 03:00 Stockholm). Don't count on the night.

**Reviews** (Decided, [docs/REVIEW.md](docs/REVIEW.md)): a Sonnet review at the end of Tue, Wed, Fri and Sun's pieces, Fable on the report page, and a fresh Opus pass on the whole repo at the freeze.

**Cut order if late:** the open-weights mode, then the cross-player summary's polish, then the event log. Never cut the checking pass or the score against Sasha's notes.

## The 3-minute demo

| Time | What |
|---|---|
| 0:00 to 0:20 | The problem: hours of footage per playtest, from a level designer |
| 0:20 to 1:20 | One session: a player gets stuck; the report shows that moment with clip, words, game state |
| 1:20 to 2:00 | How: candidates, then the checking agent dropping false alarms (show one it dropped) |
| 2:00 to 2:40 | Across players, and the score against the designer's blind notes |
| 2:40 to 3:00 | The open-weights mode, or what comes next |

Show only what was built during the event.
