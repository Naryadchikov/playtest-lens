# 25: Lobby report fixes, the plan

Planner: Claude Opus 5.5 (medium), Cursor, 2026-10-28. Implementer: Claude Sonnet 5.5 (high). Reviewer: a fresh Grok 4.7 xhigh. Base commit: `11565d6` on `main`, plus the uncommitted `docs/tasks/25-report-feedback.md` and `DECISIONS.md` edits (read them, do not change them).

## The outcome

Sasha could not follow the player on the Lobby report's map, the section titles call every room a puzzle, and the story of getting into the Archive is split across the top and the bottom of the page. After this pass, the map has a time control: the route, the pins and the F9 markers appear as time moves. Only a volume with a puzzle line is called a puzzle. Sections run in time order, so the bathroom vent at 7:05 sits right before the camera and the bear trap at 7:24. All of it is proven by re-running the deterministic beats step and the renderer on the existing `runs/check/cogito-findings.json`, with no model call.

Part B lists the judgment problems that need a new checker pass later. This pass writes nothing for Part B except the follow-up lines named at the end.

## Rules for the implementer

- Do not call any t3-code tools. Never run `rm`. Do not commit. Never use `--yolo` or any flag that turns off approvals or the sandbox.
- No model call of any kind: no Meta API, no Baseten, no Modal. Never run `analyzer/check.py` or `analyzer/spark_test.py`. Never read the Keychain.
- Follow `.claude/skills/change-analyzer/SKILL.md` for `analyzer/beats.py`, then `.claude/skills/validate-change/SKILL.md` before you report.
- No em dashes and no spaced en dashes anywhere you write, code comments and strings included.
- Report at the end: files changed, commands run with exit codes, the evidence paths, and what you did not check. No file dumps.

## Sasha's words (quoted from `docs/tasks/25-report-feedback.md`, Cursor chat, 2026-10-28)

The map:
- "having some timeline or filtering on 2d map will be nice, now it looks a bit too messy and not really readable."
- "it is almost impossible to follow the route of the player since things are just overlapping, I think having timeline and scroll and see things appear will be great."
- "I still think we can make it better on 2d side inside the report." Not a Godot editor overlay.

Puzzles:
- "why we still have things called puzzle 1, etc."
- "there is only one puzzle essentially in the lobby area, and it is code lock, and I only have one volume with filled puzzle line, so I guess we should stop treating everything as puzzle."
- Finding the real CEO laptop "could be" another puzzle. He did not mark that volume as a puzzle.

Order:
- "we missed the good moment where I found entry to archive room by openning the vent unscrewing the screw. it should be before this one" (the camera and bear trap card).
- The Archive entry "was correctly identified, so why it is in the end, I think we need to improve on the ordering as well."

The judgment cards (Part B):
- Lobby door: "I would not say it actually as important, it is just part of the world building I guess, closed door, that is it, maybe ok to flag in regards to nice to explain more why it is locked, but not really stuck flag with medium sevirity to my taste."
- CEO door: he "aknowledged that I know that key probably can open the door, and decided to open it myself with the unlock mechanic and the pin, so I solved it, seems that the model havent looked further and cut early."
- Lockpick: "I have managed to do it without a real struggle."
- Archive name: "I think this one should have picked the name of the volume, that is break room, why it is not?"

Already decided, still binding (DECISIONS.md): "the report hierarchy is Area, Puzzle, Attempt, Sub-beat. An Attempt is one visit to the same Puzzle in the same Area." This plan keeps that for puzzles. A room without a puzzle line is an Area visit, not a Puzzle, so it has no Attempts.

"I guess" and "could be" above are not locks. This plan reads "stop treating everything as puzzle" for the Lobby's zoned sessions only, and leaves sessions without a log (Talos) as they are.

## What the file holds today (checked by the planner)

- `route.points` are `[t, x, z]` in video time (first `t` 26.21, last 492.98, 464 points). Pins use `time_s` and `at`. `markers` is empty in this file. `route.heat` spots have `x`, `z`, `r_m`, `seconds` and no time.
- `rank` is the order of kept findings in time (`analyzer/check.py` `run_checks`: `rank = kept`). So rank is not what buries a card. The cause is grouping: the render groups by `(area, puzzle, zone, puzzle_number)` and places a group where its first card sits. The zoned "Archive" with an empty puzzle line becomes area Archive, puzzle "Archive", "Archive, Puzzle 1", and gathers three separate visits: 0:48 (fridge, vending machine), 2:52 (laptop rejected) and 7:12 (camera, bear trap). That section is second on the page. The bathroom duct moment (rank 17, 7:05, "oh wait, I can spin it", the checker's game_state names `BATHROOM_STALL2/DuctDoor`) is its own "Bathroom, Puzzle 1: Access Archive" section near the end.
- So the vent moment is probably not missing: it is rank 17, worded as "hidden bathroom wall panel spins open", and placed far from the camera card. The planner did not watch the video. The orchestrator confirms at 7:00 to 7:12 of `recordings/cogito/cogito.mp4` after this pass.
- Every zone in the log has an empty puzzle except `Code Lock` (zone `Archive`). `analyzer/beats.py` `zone_intervals` keys open zones by name only, so the overlapping `Archive` boxes at log t 472 to 482 (one with `Code Lock`, one without) overwrite each other. No kept finding falls there; dropped 478 s does.

## Part A: page and beat changes, proven with no model call

### A1. Beats: a puzzle only where the volume's puzzle line is set

File: `analyzer/beats.py`.

When `assign_beats` gets a non-empty `zones` list (the session has a log with volumes):
- A kept finding inside a zone whose `puzzle` is non-empty gets `beat.puzzle` = that puzzle line, a `puzzle_number`, and its `attempt`, as today.
- Every other kept finding (inside a zone with an empty puzzle line, or outside every zone) gets `beat.puzzle` = null, `beat.puzzle_number` = null and `beat.attempt` = null. It keeps `area` (the zone name inside a zone, else the checker's area as today), `zone`, `attempt_start_s`, `attempt_end_s` (the visit's span, from the zone interval or the occurrence, as today) and `index`.
- Puzzle numbers count only puzzles that get a number, so the Lobby's Code Lock becomes "Puzzle 1", not "Puzzle 2".
- The internal states and the departure logic stay as they are. Change only what is written into `beat`, and where numbers are assigned. Do not delete the fuzzy matching (it serves Talos; its limits are in `docs/FOLLOWUPS.md`).

When `zones` is empty or None (no log, the Talos files), behavior is unchanged. Sasha decided the Talos grouping ("Yellow Puzzle Area, Puzzle 1, Attempt 1").

`zone_intervals`: key open zones by `(zone, puzzle)` instead of `zone`, so two boxes with one name and different puzzle lines no longer overwrite each other. This happened in this log (t 472 to 482).

Add a CLI on the same functions, the way `analyzer/spatial.py` has one: `python -m analyzer.beats <findings.json> --log <session.jsonl> --video-flash-s <seconds> -o <out.json>`. It loads with `analyzer.findings.load`, reads the log with `analyzer.log_candidates.load_log`, calls `zone_intervals` then `assign_beats` (the two calls `analyzer/check.py` makes, nothing else), writes the file, and re-validates it with `analyzer.findings.load`. It imports no model client. It refuses to write over its input when `-o` is missing (print a clear message, exit 1), so the original findings file stays as Sasha saw it. This is the same step re-run, not a second path.

### A2. Section titles

File: `report/render.py`, `_group_title`.

- "Puzzle {number}: {puzzle}" only when the beat has both `puzzle` and `puzzle_number`.
- A beat with `puzzle` null shows the area name only ("Archive", "CEO Office", "lobby").
- Remove the bare "Puzzle {number}" branch (`elif number is not None`): after A1 a numbered beat always has a puzzle.
- `_pin_title` follows the same rule: the area when `puzzle` is null.
- The page shows the volume name as written. The 0:48 room is a volume named "Archive" in Sasha's scene (`game/addons/cogito/DemoScenes/COGITO_3_Lobby.tscn`, commit `8049b5d`); there is no "break room" volume. That is his to rename in the scene. This pass does not touch `game/`.

### A3. Order and grouping

File: `report/render.py`, `_beat_key`, `_kept_groups`, `_render_groups`, `render_html`.

- A puzzle beat (`puzzle_number` not null) groups as today: one section per `(area, puzzle)`, its Attempts nested inside, in attempt order (the decided hierarchy).
- A beat with `puzzle` null groups per visit: key `(area, zone, attempt_start_s)`. One section per visit, no "Attempt n" heading. Its note is the existing `moments.note` ("N moments, m:ss-m:ss").
- Sections run in time order: sort by the section's start, which is what `_group_span` already returns (earliest `attempt_start_s`, else `time_s`). Ties go to the lower rank.
- Cards inside a section or an attempt run by `time_s`, ties by rank.
- The open section stays the one holding the lowest rank (unchanged rule).
- Update the module docstring: order now comes from the file's times and beat fields.

Expected Lobby sections after A1 to A3 (the implementer checks the real output against this): lobby 0:36; Archive 0:48 (ranks 2, 3); CEO Office 1:57 (4, 5); Archive 2:52 (6); CEO Office 3:18 (7); CEO Office 3:52 (8); Office Complex 4:51 (9); then the paper hunt and CEO Office visits at 5:14 to 5:27 (10, 11, 12); Archive, Puzzle 1: Code Lock 5:39 to 6:01, Attempts 1 and 2 (13, 14); Office Area 6:09 (15, 16); Bathroom 7:05 (17); Archive 7:12 (18); Laboratory 8:16 (19); the last visit at 8:22 (20). Two neighbouring "CEO Office" sections at 3:18 and 3:52 are expected; do not merge them in this pass (follow-up below).

### A4. Time control on the map

File: `report/render.py` only (markup, `STYLE`, `LABELS`, one inline script).

What it does:
- Below the map, inside the map's column: a Play/Pause button, a range input, and a readout "m:ss of m:ss". Range `min="0"`, `max` = `session.duration_s`, `step="1"`, initial value = `max`, so the page opens on the whole route as today (Opus's proposal; Sasha may prefer it to open at 0:00).
- Moving the slider to time T shows: the route up to the last point with `t <= T`; arrows whose point has `t <= T`; pins with `time_s <= T`; F9 markers with `t <= T`; a "now" dot at the last route point with `t <= T`. The end circle and its "end" label show only when T reaches the last point's `t`.
- Heat is not tied to the slider. Sasha, Cursor chat, 2026-10-28: "lets have timeline view without the heat" and "we can have it as toggle, and then this toggle should sum everything, so on paper being by the end of timeline". The timeline never draws heat, including at the end. A separate toggle, off by default, shows the full-session heat already in `route.heat` (the sum), at any slider time. Wording of the toggle is a proposal in `LABELS`.
- Pin list entries with `time_s > T` get a dimmed class. They stay links to their cards.
- Play advances T at 10 times real time (a named constant in the script, Opus's proposal; 512 s plays in about 51 s). Play at `max` restarts from 0. Pause stops. Dragging the slider pauses.

How it is built:
- Each route polyline keeps its full `points` (the view without script) and gains `data-t`: the route times in the same order, written from `route.points`. Pins get `data-t="{time_s}"`, F9 markers `data-t="{t}"`, arrows `data-t` of the point they sit on. The heat group gets a class the script toggles. The "now" dot is a `<circle>` the script moves to an existing route point's pixel position (no interpolation).
- The controls are rendered with the `hidden` attribute and the script removes it, so a reader without script, or a print, sees today's full map and no dead controls. Hide the controls in `@media print`.
- One inline `<script>` before `</body>`: no network, no `eval`, no `innerHTML`, no `javascript:` URL. It reads `data-t` attributes, sets `points`, toggles a class or `hidden`, and writes the readout with `textContent`. About 60 lines.
- New words go in `LABELS["timeline"]`: the button's "Play" and "Pause", the slider's accessible name "Time in the recording", and the readout "{time} of {duration}". Pass Play and Pause to the script through `data-` attributes so no wording lives in the script. These strings are Opus's proposals; Sasha decides every word the user reads.
- Map legend: add one line for the "now" dot (proposal wording: "Where the player is at the slider's time").
- `LABELS["moments"]["sub"]` now says the wrong thing ("Grouped by area, puzzle and attempt. The worst puzzle is open."). Proposal: "In time order. A room with a puzzle line groups its attempts. Time is from the recording's start flash." Put it in, list it for Sasha.

The page stays a renderer. The script shows or hides route points, arrows, pins, markers and heat, and moves a dot to a route point, all from times already in the file. It never invents a finding, a time, a position or a count, and shows no "N of M shown" text.

"No JavaScript at all" was a rule in the task 23 brief, not a decision of Sasha's. A timeline he can "scroll and see things appear" needs a small script. This plan changes that rule; the reviewer checks the script against the limits above.

The upper floor: a time scrubber does not split floors; the CEO office still lies on the ground plan, and that stays in `docs/FOLLOWUPS.md`. No second map in this pass.

### Files

May touch:
- `analyzer/beats.py`
- `report/render.py`
- `tests/test_beats.py`, `tests/test_report.py`, and new fixtures under `tests/fixtures/` if a test needs one
- `docs/FOLLOWUPS.md` (append the lines listed at the end)
- `docs/tasks/25-report-plan.md` (append "What came back" at the end only)
- New output files `runs/check/cogito-findings-25.json` and `runs/check/cogito-report-25.html` (git-ignored)

May not touch:
- `game/` (the submodule) and anything under it
- `analyzer/prompts/`, `analyzer/check.py`, `analyzer/spark_test.py`, `analyzer/client.py`, `analyzer/spatial.py`, `analyzer/summary.py`, `analyzer/findings.py`
- `runs/check/cogito-findings.json`, `runs/check/cogito-report.html`, the clips, `recordings/`
- `DECISIONS.md`, `docs/tasks/25-report-feedback.md`, `AGENTS.md`, `STATUS.md`

If a change seems to need a file on the second list, stop and say so in the report.

### Tests (offline, no API)

`tests/test_beats.py`:
- With zones where one has a puzzle line and one does not: the finding in the puzzle zone has `puzzle` and `puzzle_number` 1 and an `attempt`; the finding in the empty zone and an unzoned finding have `puzzle`, `puzzle_number` and `attempt` null, and keep `area`, `zone`, `attempt_start_s`, `attempt_end_s`.
- An empty-puzzle zone visited twice gives two distinct `attempt_start_s` values.
- Two overlapping boxes with one zone name and different puzzle lines give two intervals with their own start and end (the `(zone, puzzle)` key).
- No zones: the existing tests pass unchanged. Update only the tests whose zoned expectations A1 changes (for example `test_zone_visits_number_in_time_order_with_unzoned_moments` and `test_same_puzzle_outside_zone_continues_attempt_count`, where an unzoned moment now has no puzzle), and say which in the report.
- The CLI: on `tests/fixtures/spatial_findings.json` with `tests/fixtures/spatial_log.jsonl` (or a small new fixture), writes a file `analyzer.findings.load` accepts; with no `-o` it exits 1 and leaves the input unchanged.

`tests/test_report.py`:
- Replace `test_groups_and_cards_follow_beat_and_rank` with a time-order test on `findings_redesign.json`: sections "Hall, Puzzle 1: badge reader", "North room, Puzzle 2: weighted plates", "South room, Puzzle 3: crate shelf"; cards `5, 8, 9, 2, 1, 3, 7, 6, 4`; the open section is North room (it holds rank 1).
- A beat with `puzzle` null renders the area alone, with no "Puzzle" text and no "Attempt" heading; two such visits to one area render as two sections in time order.
- Replace `test_page_has_no_javascript` with: exactly one `<script`, no `src=`, no `javascript:`, no `eval(`, no `innerHTML`, no `http` URL.
- Every pin, F9 marker and arrow carries a `data-t` equal to its time in the file; each route polyline's `data-t` lists the route times in order and its `points` are still the full route (the no-script view).
- The timeline controls carry `hidden` in the markup; pages with no map (`findings_sample.json`, `findings_sample_b.json`) have no timeline controls and no script.
- The heat group has the class the script toggles.

Run: `.venv/bin/python -m pytest -q`. All pass, with no network.

### What done looks like

1. `.venv/bin/python -m pytest -q` passes. Give the count.
2. `.venv/bin/python -m analyzer.beats runs/check/cogito-findings.json --log recordings/cogito/2026-10-28T20-31-08Z.jsonl --video-flash-s 25.2 -o runs/check/cogito-findings-25.json` exits 0.
3. `.venv/bin/python -m report.render runs/check/cogito-findings-25.json -o runs/check/cogito-report-25.html` exits 0.
4. From the new page, list the section titles in order with their notes, and compare them with the expected list in A3. Only "Archive, Puzzle 1: Code Lock" says "Puzzle".
5. `runs/check/cogito-findings.json` is byte-identical to before (`git diff` cannot see it: compare a `shasum` taken before and after).
6. Three kept findings picked at random read the same in `cogito-report-25.html` as in `cogito-findings-25.json` (time, summary, quote).
7. Open the page in a browser with a throwaway profile, if one is available to you: screenshots at slider 0:00, about 2:00, 7:10 and the end, saved under `runs/check/25-shots/`. If you cannot open a browser, say so; the orchestrator does it.
8. `git diff --stat` shows only files from the "may touch" list. No key, token, home path, video or audio in the diff. No em dash or spaced en dash in the diff.

## Part B: judgment problems for a later checker pass (do not implement, do not run)

These need a new checker run on the video, which costs Meta credits and is the orchestrator's to start after the review. Each names the file to change.

B1. CEO door judged stuck when he chose to solve it (rank 4, 1:57). The log shows the lockpick finishing after the clip: `lock` false at video 132.2 s and `door` open at 133.5 s, while the clip is 107 to 127 s. The checker "cut early". Change: `analyzer/check.py` `slice_for` adds a short "after the clip" section, the log's `lock`, `door`, `keypad`, `quest`, `pickup` and `zone_enter` lines up to 15 s after the clip end (15 is a proposal); `analyzer/prompts/check.md` says to read it only for `resolved`, and that a player who states a plan and then carries it out is not stuck.

B2. Lockpick judged a struggle (rank 5, 2:05). He says it was not. Change in `analyzer/prompts/check.md`: a minigame finished within the clip, without repeated failure out loud, is `learning`, and drops unless the player shows confusion or surprise. Ranks 4 and 5 are 8 s apart on the same door; a later look may merge such pairs at the candidate step (`analyzer/spark_test.py`), which is a separate question.

B3. Lobby door judged stuck at medium friction (rank 1, 0:36). His words leave it open ("maybe ok to flag ... nice to explain more why it is locked"). Change in `analyzer/prompts/check.md`: a locked door tried a few times and left, with nothing pointing the player to it, is `learning` at most. Whether to keep it as a "why is it locked" note is Sasha's call.

B4. The vent. Rank 17 (7:05) is probably the vent: "oh wait, I can spin it", `BATHROOM_STALL2/DuctDoor` opens, `demo_access_archive` completes. A3 puts it right before the camera card. If the video at 7:00 to 7:12 shows a screw on a vent, the summary's "hidden bathroom wall panel" wording is the checker's, and the fix is in `analyzer/prompts/check.md`: name the object from the log path when the picture is unclear. If the video shows a separate screw moment that no candidate caught, it goes to the candidate prompt `analyzer/prompts/spark_test.md` as a missed "good moment" (a found shortcut or hidden route). The kinds are stuck, confused, surprised and suspected_bug; filing a discovery as `surprised` is Opus's proposal, a new kind is Sasha's call.

B5. The crash cards say Unity (ranks 19 and 20: "Unity Editor", "Unity debugger"). The game is COGITO in Godot. The log's `session_start` line carries `godot_version` ("4.7.2-stable (official)"). Change: `analyzer/check.py` `build_prompt` fills a new `{engine}` field from `session_start` (for example "Godot 4.7.2-stable"), or "unknown" without a log; `analyzer/prompts/check.md` says "The game runs in {engine}. An editor or debugger on screen is that engine's." Also in `analyzer/prompts/spark_test.md` if its replies name an engine.

Per the change-analyzer skill, each prompt change is committed with the run that motivated it and its before and after findings, on the tuning sessions only.

Questions for Sasha, from this plan (numbered, Opus's recommendation each):
1. The 0:48 room is a volume named "Archive". Is it the break room, to rename in the scene? Recommendation: rename it on Windows; the page will show the new name.
2. Should the map open at the whole route (as today) or at 0:00? Recommendation: whole route, with Play.
3. Heat layer while scrubbing: only at the end, or always? Recommendation: only at the end, since it has no time.
4. The CEO laptop room "could be" a puzzle: mark its volume's puzzle line if you want it shown as one. No code change needed.

## Follow-ups to append to `docs/FOLLOWUPS.md`

- Neighbouring sections with one area name (two "CEO Office" sections at 3:18 and 3:52) could merge on the page. Left as two. From task 25, 2026-10-28.
- A "recent trail only" option on the map timeline (show only the last N seconds of route) if the growing route still overlaps. Sasha's call on N. From task 25, 2026-10-28.
- Unzoned moments in a zoned session still take the checker's free area wording ("Central Office - Meeting Room Hunt", "Office Complex"), and the fuzzy matching can file a later moment under an older wording (rank 20 at 8:22, the crash, lands in the paper hunt). From task 25, 2026-10-28.

## What came back

(The implementer appends: files changed, commands with exit codes, the section list from step 4, evidence paths, what was not checked. The orchestrator appends what it changed.)

### Implementer, Part A (Claude Sonnet 5.5 high, Cursor, 2026-10-28)

Files: `analyzer/beats.py` (A1 and the CLI), `report/render.py` (A2, A3, A4), `tests/test_beats.py`, `tests/test_report.py`, `docs/FOLLOWUPS.md` (the three lines). Not committed. Two writers touched `tests/test_beats.py`, `tests/test_report.py` and `docs/FOLLOWUPS.md` during the run (another agent's edits landed in them); the final tests are the ones in the tree, and the orchestrator should read them rather than trust this note.

Commands:
- `.venv/bin/python -m pytest -q`: 178 passed, 1 failed (exit 1). The failure is `tests/test_transcribe.py::test_extract_audio_from_say_clip` (`assert (None is not None)`, audio extraction from a `say` clip). That file and the code it tests were not touched; the cause (sandbox or the machine's tools) was not investigated.
- `.venv/bin/python -m analyzer.beats runs/check/cogito-findings.json --log recordings/cogito/2026-10-28T20-31-08Z.jsonl --video-flash-s 25.2 -o runs/check/cogito-findings-25.json`: exit 0.
- Same command without `-o`: exit 1, "-o is required: this tool never overwrites its input file."
- `.venv/bin/python -m report.render runs/check/cogito-findings-25.json -o runs/check/cogito-report-25.html`: exit 0.
- `shasum runs/check/cogito-findings.json` before and after: `e6c7dd3abf7bb5417ccd4854646298eb669587da`, unchanged.

Section list from `runs/check/cogito-report-25.html` (16 sections, same as the A3 list): lobby 0:36-0:36; Archive 0:48-1:43 (2 moments); CEO Office 1:57-2:05 (2); Archive 2:52-3:14; CEO Office 3:18-3:51; CEO Office 3:52; Office Complex 4:51; Central Office - Meeting Room Hunt 5:14; CEO Office 5:19-5:24; Central Office - Meeting Room Hunt 5:27; Archive, Puzzle 1: Code Lock 5:39-6:01 (2 attempts, 2 moments); Office Area 6:09-6:16 (2); Bathroom 7:05; Archive 7:12-7:53; Laboratory 8:16; Central Office - Meeting Room Hunt 8:22. Only "Archive, Puzzle 1: Code Lock" says "Puzzle". The bathroom (rank 17) sits right before the Archive camera card (rank 18). Card ids run 1 to 20 in order.

Spot check: ranks 13, 1 and 7 read the same in the page as in `cogito-findings-25.json` (summary and quote).

Evidence: `runs/check/cogito-findings-25.json`, `runs/check/cogito-report-25.html`.

Existing tests changed because A1 changes zoned expectations: `test_zone_visits_number_in_time_order_with_unzoned_moments` and `test_same_puzzle_outside_zone_continues_attempt_count` (now an unzoned moment has no puzzle). In `test_report.py`: `test_groups_and_cards_follow_beat_and_rank` and `test_page_has_no_javascript` were replaced, and `test_every_string_from_the_file_is_escaped` now checks the raw payload is absent (the page has one script tag now).

Not checked: no browser was opened and no node is installed, so the script has never run (not even a syntax check) and there are no screenshots under `runs/check/25-shots/`. The orchestrator must do step 7. `git diff` was not scanned for tokens by a tool beyond a grep for em dashes, home paths and key words (no hits in analyzer, report, tests, FOLLOWUPS).

Plan notes: (1) The plan's "Archive 0:48 (ranks 2, 3)" matched. (2) The plan says the bare "Puzzle {number}" branch is removed; a numbered beat whose puzzle equals its area would now read "Archive, Puzzle 1: Archive". No file in the tree has this after A1. (3) `zone_intervals` keys by `(zone, puzzle)`, so a `zone_exit` with a different puzzle line than its enter would not close it; the real log always repeats the line.

### Implementer, Part A, final pass (Claude Sonnet 5.5 high, Cursor, 2026-10-28)

This entry supersedes the one above where they differ (the one above was written while a second writer was editing the same files). It covers the heat decision (Sasha, Cursor chat, 2026-10-28: "If you mean heatmap view, I think we can have it as toggle, and then this toggle should sum everything, so on paper being by the end of timeline, but lets have timeline view without the heat then.").

- Heat: the slider never touches it. The heat group is `<g class="heat">`; the page without script shows it, as before. When the script runs it hides the heat and a checkbox "Heat, whole session" (off by default, only rendered when `route.heat` is not empty; wording in `LABELS["timeline"]["heat"]`, marked a proposal) shows or hides the whole-session heat at any slider time. The map still opens on the whole route (slider at the end).
- Files: `analyzer/beats.py`, `report/render.py`, `tests/test_beats.py`, `tests/test_report.py`, `docs/FOLLOWUPS.md`. Nothing committed. `game/` and the prompts untouched.
- `.venv/bin/python -m pytest -q`: in the sandbox, 178 passed and 1 failed (exit 1): `tests/test_transcribe.py::test_extract_audio_from_say_clip`, which needs macOS `say` and fails only in the sandbox. Run outside the sandbox, `tests/test_transcribe.py` gives 8 passed (exit 0). `tests/test_beats.py` 32 passed, `tests/test_report.py` all passed.
- `analyzer.beats` CLI on the real findings with `-o runs/check/cogito-findings-25.json`: exit 0. Without `-o`: exit 1, input unchanged (also tested, and `-o` equal to the input is refused). `report.render` to `runs/check/cogito-report-25.html`: exit 0. `shasum runs/check/cogito-findings.json` before and after: `e6c7dd3abf7bb5417ccd4854646298eb669587da`, identical.
- Section list: the same 16 sections as the entry above, in the A3 order; only "Archive, Puzzle 1: Code Lock" says "Puzzle". The A3 text says "the paper hunt"; the page shows the checker's wording "Central Office - Meeting Room Hunt" (5:14, 5:27, 8:22).
- Script check without a browser or node: `/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc` ran the script against a hand-made stub of the DOM (`runs/check/25-stub.js`, git-ignored). Result: at the start the heat and the "now" dot are hidden by the script and the controls unhidden; at slider 120 s the route is cut to 94 points, the dot moves to the 94th point, only pins with `data-t <= 120` show; at 0 the dot hides; ticking the heat box shows heat and it stays as set when the slider moves to the end. This is a stub, not a page in a browser.
- Not checked: no browser screenshots (`runs/check/25-shots/` does not exist), Play (needs `requestAnimationFrame`, the stub does nothing for it), print view, the dark theme, keyboard use of the slider. The orchestrator does step 7.
- Plan notes: (1) A3 says "the paper hunt" but the page shows the checker's own words. (2) Removing the bare "Puzzle {number}" branch means a numbered beat whose puzzle equals its area reads "Archive, Puzzle 1: Archive"; no file in the tree does this after A1. (3) `zone_intervals` keyed by `(zone, puzzle)` would not close a zone whose exit line carries a different puzzle line than its enter; the real log repeats it. (4) The plan's "heat group gets a class the script toggles" now means: the script adds the hiding class on load, the checkbox removes it.
