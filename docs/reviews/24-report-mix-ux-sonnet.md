Reviewer: Claude Sonnet 5.5, Claude Code via T3. Commit 17a9675 (task 37, Claude Fable 5.1). UX review with a score.

I used the pages as a first-time level designer would: Chromium and WebKit through Playwright, from file://, at 1920 x 1080, 1440 x 900, 960 x 1080 and 400 px, light and dark. I ran the seven points as tasks and played her Spark session for 60 s at 10x. No console or page errors in either engine on any of the four pages. Captures are in `/tmp/r24/shots/`, scripts in `/tmp/r24/s/`. Nothing was copied into the repo.

## Score

| # | Point | Score | Why |
|---|---|---|---|
| 1 | Knows what went wrong and where in a few seconds | 8 | Verdict line, five ranked problems with kind shapes, and the map with pins all fit the first 1080 px. The faint route is a dark web that competes with the pins. In his demo session the #1 problem pin is cut off at the map edge. |
| 2 | Problem to clip in one click, back in one | 7 | One click opens Watch and Escape or Back closes it. Back returns to the moment's row in the long list (scrollY 0 to 1339), not to the problem or map the reader came from. |
| 3 | At a moment: big clip, words, cause, where, nothing repeated | 7 | The layout is right: clip about two thirds wide, the quote as headline, summary and "Likely cause" under it. The Play/Pause button cannot be read, and the context header can name a different place than the caption ("Archive" over "Code Lock"/"Laboratory"). |
| 4 | Can play the session and understand what happens between moments | 7 | The walking state is clear: a big clock, "Up next: moment 4 at 3:52, Code Lock", a progress bar, the floor following, the events so far. It stops at 4 and 7 only, as decided. Pause is unreadable, Space closes Watch, and the left half is empty while walking. |
| 5 | Finds a dropped candidate and its reason without hunting | 7 | The reason shows in Read and in Watch, and hollow pins on the map open it. The first screen never links to the Dropped section, which starts about 5900 px down on her page. |
| 6 | Never wonders which mode they are in | 8 | Read is a page, Watch is full screen with Back and "Moment 4 of 24" on top. The hash and focus follow. Space (the play key) closes Watch right after opening, which is a mode surprise. |
| 7 | Holds at 960 and on a phone | 8 | No horizontal overflow at 960 or 400 in Read or Watch. At 960 the clip stays big and the map is small but usable. At 400 Read is clean, and Watch works but its timeline labels pile up. The Open page cannot be told from the Spark page above the fold. |
| | **Overall** | **7.4** | Mean of the seven. |

**NOT PASS.** Five points are below 8, and one defect blocks (the Play/Pause button, defect 1).

## The two things the orchestrator noticed

1. **The Pause button looks disabled while a clip plays: confirmed, and it is worse.** The button is unreadable in every state, paused or playing, light and dark, Chromium and WebKit. It is not disabled (`disabled` is false and clicks work). Measured text on background contrast: dark 1.25:1 (`rgb(11,16,32)` on `rgb(32,38,54)`), light 1.16:1 (white on `rgb(236,238,242)`); the same numbers for "Play" and "Pause". Cause: `.bar .nav button` (specificity 0,2,1, `report/render.py:357`) sets `background: var(--sunk)` and wins over `.primary` (0,1,0, line 260), so the accent background is lost while `color: var(--on-accent)` stays. Capture: `/tmp/r24/shots/hs-1920-light-watch-m4-playing.png` (an empty slot between Previous and Next), and the top bar of `/tmp/r24/shots/hs-1920-dark-watch-m4-t2.5.png`.
2. **The faint whole route competes with the 30 s trail: partly confirmed.** In Watch the trail wins: it is white and thick, and it was readable at 1920, 1440 and 960 on both floors (`hs-1920-dark-watchmap-m11.png`, `hs-960-dark-watch-m4.png`). The route is still the heaviest ink on the map. Each segment has a black outline (`.route .case`, 16 wide at 50% black) under a pale line at 32%. In dense rooms (Break Room, Archive) it becomes a dark mesh. It hides the room plan and sits on top of small pins 14, 15, 19 and the hollow dropped markers (`hs-1920-dark-ovmap-2x.png`, `hs-1440-light-noscript-top.png`). On the Read map there is no trail, so the route is the main texture. It competes with the pins there, not with the trail.

## Defects, most severe first

1. **Play/Pause is unreadable (blocking).**
   - Size and state: all sizes, both themes, both engines, always (paused and playing).
   - What happens: see "The two things" above. The main playback control looks like an empty slot or a disabled button.
   - Capture: `hs-1920-light-watch-m4-playing.png`, `hs-960-dark-travel.png`.
   - Why it matters: a designer cannot find the one control that starts or pauses the session. The video plan shows exactly this bar.
   - Fix: `.bar .nav .primary { background: var(--accent); color: var(--on-accent); }` (or raise its specificity). Add a test on the computed contrast.

2. **Space closes Watch right after it opens.**
   - Size and state: any size. After any click that opens Watch, focus is on Back (`openWatch` focuses `#back`). The key handler skips buttons (`render.py:1601`), so Space presses Back.
   - What happens: click a top problem, press Space: Watch closes and the clip is paused (Chromium and WebKit, `/tmp/r24/s/space.py`). The hidden hint says "Space plays and pauses".
   - Why it matters: Space is the first key anyone presses on a video. It sends the reader out of the player.
   - Fix: on open, focus Play or the clip region instead of Back, and let Space on Back still toggle play (Enter keeps activating Back).

3. **Back returns to a different place than the one the reader left.**
   - Size and state: 1920, from a Top problems row, a badge or a map pin (the first screen).
   - What happens: click "Archive, Code Lock" (scrollY 0), then Escape: Read scrolls to the moment's row (scrollY 1339) and focuses its Watch button. Same for badge 7 (scrollY 2421). From a moment thumbnail it is right.
   - Capture: `hs-1920-dark-after-back.png`, numbers from `/tmp/r24/s/tasks.py`.
   - Why it matters: point 2 asks for "back in one". The reader loses the ranked list and the map and must scroll up to pick the next problem.
   - Fix: store `scrollY` and the opener when opening; if the opener is in Top problems or the map, restore that position and focus the opener.

4. **His demo session: the #1 top problem is half off the map.**
   - Size and state: 1920 and 960, Read and Watch, `cogito-muse-spark-1.2-contributor-report.html`.
   - What happens: moment 8 (suspected bug, Laboratory) is at x = -7.6 in a 1334-wide viewBox. The pink triangle is cut by the left edge, and the route leaves the plan to reach it. In Watch the header above the map says "Archive, Ground floor" and "8:02 Archive door unlocked" while the caption says "Laboratory". The two are both true (clip start versus moment) but nothing says so.
   - Capture: `ds-1920-dark-pin8-crop.png`, `ds-1920-dark-watch-m8.png`, `ds-1920-dark-read-top.png`.
   - Why it matters: this page is the public demo and the GIF, and the worst problem is the one you cannot see.
   - Fix: clamp off-plan pins into the viewBox with a visible "outside the mapped area" edge marker, or widen the viewBox by a margin when a pin is outside. Show "Outside the map" instead of a room that contradicts the caption.

5. **The faint route is too heavy (see above).**
   - Size and state: every Read map and Watch map. Worst in dense rooms.
   - Fix: drop the black `.case` for the whole route (keep it for the trail), and lower the route to about 0.2 opacity or 4 px. Re-check that pins 14, 15, 19 and the hollow dropped pins read.

6. **The Open page and the Spark page look the same above the fold.**
   - Size and state: all sizes. The model name appears only in the footer (y about 10150 on her Open page), so at 960 x 1080 side by side nothing says which is which.
   - Why it matters: the video plan is "then Open beside it". A judge cannot tell what changed except by the counts.
   - Fix (proposal, the words are Sasha's): one line under "Session lobby-player-1" naming the model, for example "Muse Spark Open".

7. **Dropped candidates are not linked from the first screen.**
   - Size and state: all sizes. "4 dropped" in the subline and in the map legend is plain text. The section is the last thing on the page.
   - What happens: a reader who wants the reasons scrolls about 5900 px (her Spark page) or finds the hollow pins by luck.
   - Fix: make "4 dropped" a link to `#dropped` (scroll, not Watch), and add a plain "Dropped by the check" entry to the Top problems' neighbours or to the legend.

8. **While walking, the left half is empty and the overlay clashes with the clip's own controls.**
   - Size and state: 1920 and 960. At 960 the "Up next: moment 4 at 3:52, Code Lock, Ground floor" text wraps over the native progress bar and the time/play icons (`hs-960-dark-travel.png`). At 1920 the whole area under the small clip is blank (`hs-1920-dark-session-03.png`).
   - Why it matters: between moments is the least informative screen and the player has the most space there.
   - Fix: hide the native controls while travelling; use the empty column for the next moment's still, quote and "Likely cause" (see idea 1).

9. **A stale frame of the previous walk can show when a walk restarts.**
   - Size and state: seen once at 1920 in a 60 s run (state "3:41, Up next: moment 4" right after moment 4's clip ended, when it should have said 4:02 and moment 7). Not reproduced in two targeted runs in either engine. Probable cause: `startTravel` (`render.py:1500`) draws on the next frame, so the text from the earlier walk stays until then. Low severity, listed so the author can add `drawTravel()` to `startTravel`.

10. **Next from a dropped candidate jumps into the kept list.** "Dropped 1 of 4" then Next gives "Moment 12 of 24". It follows time, which is defensible, but the counter changes list without a hint. Low.

11. **400 px Watch and tap targets.** Watch at 400 works and scrolls inside, but the timeline labels collide (`0:00 2:00 4:00 ...`) and the pin badges in Read are 24 px, under the usual 44 px target. Reading only is accepted for phones, so this is low.

## Ideas that would raise the score most (all my proposals)

1. **Use the empty space while walking for "Up next".** Show the next moment's still frame, quote and "Likely cause" in the left column during travel. It fills the void, answers "what is happening", and previews the stop. Point 4 to 9.
2. **Make Back remember where you were** (defect 3) and focus the row you came from. Point 2 to 8 or 9.
3. **Lighten the route and keep the trail loud** (defect 5), then recheck the pins. Points 1 and 3 up by one.
4. **Link "4 dropped" to the Dropped section, and give the first screen one line on why moments are dropped** (defect 7). Point 5 to 8 or 9.
5. **Name the model on the page and handle off-plan pins** (defects 4 and 6). Together they make the demo session and the Open comparison read correctly on the first screen. Points 1 and 7 up by one.

## What I did not check

- Real audio, a real screen reader, real iOS Safari, Firefox, and a real phone. Phone sizes are 400 px viewports in Chromium and WebKit.
- Playing a whole session to the end, the upper-floor-only moments in Read, and Open pages in Watch beyond one moment each (m1) and the first screens.
- The two Open pages at 1440 and 400, and his pages at 1440, 400 and light.
- Reduced motion, print, and keyboard-only use beyond arrows, Space, Escape and Tab order.
- Wording, names and the look: those are Sasha's call. I did not compare to the mocks, the code correctness, or the numbers against `findings.json` (that is Grok's review).
- The flow recording `/tmp/t37/flow.webm` and the claim of captures in `/tmp/t37/shots/`.
