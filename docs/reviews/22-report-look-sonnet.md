Reviewer: Claude Sonnet 5.5, Claude Code. Commit 6847e40 (task 30 by Claude Opus 5.5, task 32 by Claude Fable 5.1). Look and UX review; the look and the wording are Sasha's call.

**NOT PASS: 2 blocking defects.**

Captures are in `/tmp/r22/shots/` (outside the repo). Pages re-rendered from the two findings files into `/tmp/r22/spark.html` and `open.html`, clips linked from `runs/check/lobby-player-1-clips`. Chromium for most flows, WebKit for the 960 and 400 flows. Sizes 1920 x 1080, 1440 x 900, 960 x 1080, 400 wide, light and dark. No page errors in any run.

## Blocking

**B1. Picking a problem makes the stage flicker through a wrong moment.**
- Size and state: 1920 x 1080 light (Chromium), also seen in the 400 px run. Click "1. Break Room" in Top problems.
- What happens: the page smooth-scrolls about 5300 px to moment 11's card. Near the end the scroll sync takes over: the counter went 11, 11, 11, **10**, 11 (sampled every 250 ms). For about half a second the stage shows moment 10 (upper floor lit, ground floor dimmed), the list outlines card 10, and the foot clip reloads blank, while the side panel and counter still say 11. In `f-1920-light-chromium-01-problem.png`, taken 1.2 s after the click, the map, the list and the side panel disagree. The same happens when jumping to Dropped moments: the counter runs 14 ... 24 on the way.
- Why it blocks: this is the first click of the main flow and the video's best moment, and it breaks test 3 (one current moment that map, clip, timeline and list agree on).
- Fix: ignore scroll sync while a scroll the page started is still moving (until `scrollend`, or about 150 ms after the last scroll event), then let it resume. Or jump without smooth scrolling when the target is more than a screen away.

**B2. After a scrub, the stage keeps the previous moment's clip.**
- Size and state: 1920 x 1080 light. Press Right (moment 1), then click the timeline at about 16:46. Also happens with the heat view and the timeline.
- What happens: the map time and the side panel say 16:46, "Ground floor", "Last moment: Moment 19". The foot still shows moment 1's clip ("Clip 0:29-0:49", the Lobby frame), with a live Play button, and the list still shows moment 1 first (`stale.png`, `heat-tlclick.png`). The counter is blank, so nothing marks the clip as stale.
- Why it blocks: the clip and the map point at different times; a judge scrubbing the timeline in the video sees it.
- Fix: when the map time is not inside the current moment's clip, hide the clip or show the clip nearest to the map time. The simplest is to clear the stage clip whenever `S.cur` is null and nothing is playing, as it already does on first load.

## Smaller defects (fix before the video where marked)

1. **At 960 x 1080 the top problems are below the fold (demo, fix before the video).** The stacked stage fills the first screen (map, panel, an empty clip box, the timeline). The panel text says "Or pick a problem" but no problem is visible. Test 1 (worst first and where) passes at 1440 and 1920 but not at half a screen. `spark-960-dark-first.png`, `open-960-light-first.png`. Fix: at under 1100 px, put the top problems (or just the first two) above the stage, or move the legend and the blank clip box out so the list shows.
2. **The foot row is a blank box in the overview.** About 190 px of empty panel with the legend at the bottom, on the first screen at every size (`spark-1920-light-first.png`). The clip is the judge's focus and is empty until a moment is picked. Fix: put the legend in the toolbar or under the maps, and show the worst moment's still frame (paused) in the overview.
3. **The clip beside the map is a thumbnail.** The foot clip is about 206 x 112 px at 1920 and 960, and the native controls cover it at 960 (`f-960-dark-webkit-02-clipplay.png`). The card's own clip is larger. Fix: give the clip a bigger share of the foot row (the events chips can wrap beside it).
4. **Game event chips are cut off at 960.** The event list has `overflow: hidden` and is 117 px tall with 124 px of content; the last chip ("Picked up Health Potion", moment 11) is half hidden. Fix: allow the list to scroll, or cap it with a "+n more" chip.
5. **The event label beside the dot is cut off and raw.** At 1920 and 960 a node path such as "BREAK_ROOM/kitchenSink open..." runs past the floor's right edge and sits on top of pin 11. The chips use the same raw paths. This is the known "raw event names" item in UX_PASS.md; the clipping is the page's part.
6. **Overview and Escape leave the list where it is.** From moment 11 the page stays at scroll 369 (or 5000+) after Escape or Overview; Top problems is out of view, so "back to the start" brings back the stage but not the problem list. `kb-esc.png`. Fix: scroll to the top of the problems block on Overview (not on Escape during playback).
7. **The heat map view keeps the timeline bar.** The heat legend says the timeline is in the timeline view, yet the bar stays on screen and clicking it switches back to the timeline view (`f-1920-light-chromium-10-heat.png`). Sasha's 2026-10-28 line was that the heat map turns the timeline view off. Fix: hide the bar in the heat view, or confirm that "timeline view" meant the map's trail view and reword the legend.
8. **A dropped candidate never says "Dropped" in the stage.** The panel shows a hollow shape, the time, the kind, the summary and "Reason: ...". Only the hollow shape and the list section carry the word (`probe2-chromium.png`). Test 5 would be stronger with a "Dropped by the check" tag in the panel, and the foot row shows "Previous/Next" with no "Moment n of 24" counter (blank).
9. **400 px: horizontal scroll and a clipped panel.** Spark's page is 415 px wide at 400 (`DL.facts`, `.fric`, long snake_case words); Open's is not. The moment panel under the maps cuts its last line (`m400-problem.png`). Fix: `overflow-wrap: anywhere` on the facts and let the panel grow.
10. **Mid-word breaks in the narrow side panel.** "Cabine / tDoor" and "action_secon / dary" at 1920 and 960 (`sess-10.png`). Same fix as 9, scoped to the panel.
11. **Spacing.** The two glance tiles touch the last problem card (no gap) at 1920, 1440 and in the Open page (`open-1920-dark-first.png`).
12. **"24 24 kept, 5 dropped".** The big number repeats the first number of the sentence in the second tile (`spark-1920-light-first.png`).
13. **Small type.** Timeline room names and row labels are 10 px; pin numbers about 11 px. Readable at 1x, weak in a half-screen video. The dimmed "later" event chips look disabled and are low in contrast on the light theme.
14. **Two Play buttons in the overview.** "Play the session" and the transport "Play" do the same thing; harmless, a little noisy.
15. **A full session run is long.** The run stops at all 24 moments and plays each 20 s clip, about eight minutes (the checks above ran 33 s and moved from moment 1 to 3 as designed). For a 3-minute video the presenter needs "Unplanned only" and Next. This is question 3 in UX_PASS.md; no change needed here.

## The five tests

1. **Worst first and where: pass at 1440 and 1920, fail at 960.** The numbered problems with places, severity, stuck time and rank chips read in seconds; see smaller defect 1. The verdict line alone ("24 moments worth a look: 18 confused, 6 surprised") does not say what went wrong.
2. **Where to start: pass.** One blue "Play the session" and two lines of text; at 960 see smaller defect 1.
3. **One current moment: mostly pass, with B1 and B2.** Moment panel, map outline, timeline shading, list outline and counter agree in the normal flows (problem, Next, Previous, arrows, session play, a dropped candidate).
4. **One click to the clip and map spot, one click back: pass with defect 6.** Problem, pin, rank chip or timeline mark makes the moment current; Overview, Escape or the problem link comes back.
5. **The check is visible: pass, could be louder.** "24 kept, 5 dropped" tile, the Dropped moments section with reasons, hollow marks on the map and timeline, and the reason in the stage panel; see smaller defect 8. Quotes show next to each moment.

## What works

- Two floors with the route, the lit floor outlined and the other dimmed, at 1920, 1440 and 960; the dot and the strong trail move with the clip, and "Map follows the clip" shows during playback.
- The session run: stops at moment 1 at 0:29, plays its clip, then moves on to 2 and 3; the timeline fills and the shaded span follows.
- "Unplanned only" cuts 24 moments to 8 on the map, the timeline and the list, and Next steps through them.
- Keyboard: Right, Left, Space, Escape work as written; Space pauses and resumes the clip.
- The timeline across the page is clear at 1920 and 1440 (rooms with names, upper floor, moments in three rows, dropped hollow shapes, event ticks, axis) and stays in view.
- Kinds are never colour alone (square, circle, diamond, triangle); light and dark both hold, and the map stays dark in the light theme, which reads well.
- Open (Muse Spark Open) uses the same page; its stuck squares and five problems read the same as Spark's.

## Not checked

- No-script rendering, `prefers-reduced-motion`, and a screen reader.
- Touch input on the 400 px page, and Safari proper (WebKit through Playwright only).
- Clips outside Chromium and WebKit; a slow-loading clip.
- Light mode at 400 px beyond the first screen; the Open page beyond its first screens and one 960 capture (the Open flows were not driven).
- Contrast was judged by eye, not measured.
- The recorded flow video from task 32 and the numbers in the findings comparison.
- Whether any capture contains the tester's private video frames beyond what the page itself shows; the captures stay in `/tmp/r22/` and are not committed.

## Round 2

Reviewer: Claude Sonnet 5.5, Claude Code. Commit 5b2c281 (task 35 by Claude Fable 5.1). Look and UX review; the look and the wording are Sasha's call.

**PASS: 0 blocking defects.** Both round 1 blocking defects and the heat view are fixed in Chromium and WebKit, on the Spark and the Open page, at every size. Seven smaller defects remain, two of them worth fixing before the video (S1 and S2).

Pages re-rendered from the two findings files into `runs/check/r22b-spark.html` and `r22b-open.html` (git-ignored, the clips linked from `runs/check/lobby-player-1-clips`). Captures and scripts are in `/tmp/r22b/` (outside the repo). Sizes 1920 x 1080, 1440 x 900, 960 x 1080 and 400 px, light and dark. No page errors in any run, and no sideways scroll at any size in any state I opened. A sampler read the page state every 40 ms during each jump, so a flicker cannot hide between my readings.

### Round 1 items

- **B1 (flicker while a jump scrolls): fixed.** Clicking each Top problem and the first Dropped moment, from the top of the page: one state for the whole smooth scroll (card, counter, lit floor, clip, panel agree from the first sample to the last; 70 to 78 samples per jump, scroll ranges up to 14000 px). Chromium and WebKit; Spark at 1920, 960 and 400; Open at 960 and 1440. Round 1 saw 11, 11, 11, 10, 11 on the same click. A reader's own wheel scroll after a jump moves "now" with the middle card again, and scrolling back to the top by hand returns to the overview. Escape in the middle of a jump lands on the overview. Two fast Right presses land on moment 13 from 11 (correct).
- **B2 (stage keeps the previous moment's clip): fixed.** Right (moment 1), then a click on the timeline at 16:46 (on the events row, the rooms row and the axis): the stage shows a black box with no controls and no source, the panel reads "16:46, Ground floor, Last moment: Moment 19", the counter is empty, the list stays where it was. Same from the overview, and for a scrub to 9:59 from moment 11. Right after a scrub goes to the next moment after the map time (15), Left to the last one before it (19). `b2-spark-chromium-scrub_track_r-events.png`.
- **Heat view hides the timeline: fixed.** The bar is invisible at 1920 and 1440 (the floors keep their size), gone at 400. A click where the bar was does nothing. Picking a problem in the heat view switches back to the timeline view and shows the bar, which is sensible. `heat-spark-chromium-1920.png`.
- **1 (960 problems below the fold): fixed.** The four problems end at 575 px (Open: five, 652 px), "Play the session" is at 661 px, the stage follows. Pressing Play or picking a problem scrolls so the whole stage (floors, side panel, clip, timeline) fits in one 960 x 1080 screen (`play-spark-webkit-960-15s.png`).
- **2 (blank foot box): fixed.** The overview shows the first problem's moment on its own frame, captioned "Moment 11, Confused, 6:17", with the legend beside it. Playing it makes that moment current, scrolls the list, and the map follows.
- **3 (clip thumbnail): fixed.** 292 x 164 px at 1920, 1440 and 1080-tall; 309 x 174 at 960 (was 206 x 112); the native controls no longer cover it (they appear on hover).
- **4 (chips cut off): fixed with a caveat.** Chips scroll when they overflow; see S5.
- **5 (label beside the dot): fixed.** I played the session over events at five start times, Spark and Open, 1920 and 960: every label ("Kitchen sink opened (Break room)", "Desk opened (Meeting room)") stayed inside its floor. The words read well.
- **6 (Overview and Escape leave the list): fixed.** Both return to scroll 0 at every size. See S2 for a case where Escape is ignored.
- **8 (dropped candidate never says so): fixed.** The panel carries a "Dropped by the check" tag, the reason, and the counter "Dropped 2 of 5". `dropped-spark-chromium-1920.png`.
- **9, 10 (400 px, mid-word breaks): fixed.** No sideways scroll on either page at 400 (first screen, a moment, session play, heat). The moment panel grows. I checked every moment and every dropped candidate of both pages for a word split across two lines in the panel at 1920, 1440, 960 and 400: only hyphenated words wrap at the hyphen ("wall-mounted"), nothing like "Cabine/tDoor". No panel is clipped.
- **11, 12, 13 (spacing, "24 24 kept", small type): fixed.** 24 px between the problems and the tiles; "24 kept" with "5 dropped" under it; room names and axis are larger (12 and 11 px).
- **14, 15:** out of scope, unchanged.

### The five tests

1. **Worst first and where: pass at 960, 1440 and 1920.** Problems come first at 960 (and at 400).
2. **Where to start: pass.** One blue "Play the session"; at 960 it sits under the problems.
3. **One current moment: pass.** Panel, outlined floor, timeline shading, list outline, counter and clip agree after a problem, a pin, a rank chip, a timeline mark, Next, Previous, arrows, a dropped mark, a scrub and the session play. During the session the clip and the map time agree to about a second (S7).
4. **One click there, one click back: pass.** Overview, Escape and Left at the first moment all behave; Next at the last moment is disabled.
5. **The check is visible: pass.** Tile, Dropped section, hollow marks, and now the tag and counter in the stage.

### Blocking

None.

### Smaller defects

**S1. In "Unplanned only", a problem or rank chip that points at a hidden moment does nothing (fix before the video).**
- Size and state: any size, both pages. Spark: switch to "Unplanned only", click problem 4 "Lobby" (its first moment, 1, is "by design" and hidden): the page stays on the overview, no message. Open: problems 4 and 5 do the same. Rank chips of hidden moments (Spark 1, 2, 3, 12, 15, 16; Open 5, 10, 29, 31, 32) are dead too, though they look the same as live ones.
- Why it matters: the UX pass recommends "Unplanned only" for the video, and the problem list is the first thing a presenter clicks.
- Fix: when the target is hidden by the filter, switch the filter back to "All moments" and then jump (or hide those chips and link a problem's place to its first visible moment).

**S2. Keyboard shortcuts are swallowed after you click the stage's own controls.** `keys.py`, Chromium (WebKit does not focus them).
- After clicking "Unplanned only" (or any switch), Right and Left move the radio selection, not the moment: Right flips the filter back to "All moments". After clicking Next or Previous, Space presses the button again (moment 1 to 2) instead of pausing. After playing the stage clip with its native Play, Escape and the arrows do nothing until you click elsewhere; Escape does work after the video loses focus.
- Fix: on the page's key handler, `preventDefault` and handle Left, Right, Escape for the switch radios, and let Escape and the arrows through when the target is the stage's video; or blur the control after a click.

**S3. A black box says nothing.** `b2-...scrub...png`, `dropped-spark-chromium-1920.png`. While the session travels, after a scrub and for a dropped candidate the stage clip is a 292 x 164 black rectangle with no caption. It reads as a broken video for the ten seconds of a run. Fix: a short line inside it ("The clip plays at the next moment", "No clip for a dropped candidate").

**S4. The overview names a moment the map does not show.** The foot's frame is captioned "Moment 11, Confused, 6:17" while nothing is current and the map has no outline on 11. Small, but test 3 says one current moment. Fix: add "First problem" or outline pin 11 on the map in the overview.

**S5. The event chips scroll, with no cue.** At 1440 (and 400 for Open, none) the list is 200 px tall in a 127 px box; the last chips ("Picked up Energy Drink", 7:48) are cut by the box edge and the scrollbar is hidden on macOS. Long labels end in "..." ("Kitchen cabinet 4 opened (Break ..."). Fix: a fade or "+n more" at the bottom edge, and a `title` with the full text.

**S6. The heat view leaves a blank band under the floors at 1920 and 1440** (about 380 px, the bar's row). Intended ("its row stays"), but it reads as unfinished. Fix: show the heat legend there, or let the floors grow. Also without script the foot is an empty 200 px panel with only the legend (`noscript-spark.png`).

**S7. Map time trails the clip by about half a second to a second at the start of a clip.** At moment 1 (clip 0:29-0:49) the readout showed 0:29, 0:31, 0:32, 0:34, 0:35, 0:37 while the video time was 1.5, 3.0, 4.5, 6.0, 7.5, 9.0 s (the whole-second readout floors). Inside the 1-second bar, but I did not measure the dot against frames.

### What works (new in this round)

- 960 x 1080 now reads in one screen after a click: floors, panel, a 309 x 174 clip with the game events, the timeline, the two tiles.
- The overview's own frame plays in place and moves the list; Overview and Escape come back to the problems.
- Event labels read as words, with the room in brackets; the chips and the dot label match.
- Open (Muse Spark Open): same behavior in every flow above, five problems, 33 moments; its first-problem frame is moment 4.

### What I did not check

- `prefers-reduced-motion`, a screen reader, touch input at 400 px, and Safari proper (WebKit through Playwright only).
- Contrast by measurement (the dimmed "later" chips on the light theme look low but legible).
- Whether the dot sits on the right frame (only the readout against the video clock).
- A full session run to the last moment; I ran about 40 s of it, plus Unplanned only for 9 s.
- The 960 heat view and 960 dropped-candidate layouts beyond the sampled states; the Open page at 960 in dark beyond its first screens.
- The recorded flow video, the findings comparison and the test count from task 35.
- Whether any capture holds private frames beyond the page itself: captures stay in `/tmp/r22b/`, nothing from `runs/` is copied into the repo.

## Orchestrator's follow-up (Claude Opus 5.5, Claude Code in T3 Code)

- S1 fixed: a link to a moment that "Unplanned only" hides switches the filter back to all moments, then picks it.
- S2 fixed: a mouse click on the stage's buttons or switches gives focus back to the page, so the arrows, Space and Escape keep working; Escape now works while the clip has focus. Keyboard users keep their focus.
- Checked with Playwright in Chromium and WebKit at 1920 x 1080: chip 1 under "Unplanned only" goes to `#m1` with the filter on all; after clicking Next, the right arrow steps from moment 2 to 3 and the filter stays put; Escape with the clip focused returns to the overview.
- S3 to S7 are left for the freeze pass, listed in docs/FOLLOWUPS.md.
