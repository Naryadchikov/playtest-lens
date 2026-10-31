Reviewer: Claude Sonnet 5.5, Claude Code. Commit 6847e40 (task 30 by Claude Opus 5.5, task 32 by Claude Fable 5.1). Look and UX review; the look and the wording are Sasha's call.

**NOT PASS: 2 blocking defects.**

Captures are in `/tmp/r22/shots/` (outside the repo). Pages re-rendered from the two findings files into `/tmp/r22/spark.html` and `open.html`, clips linked from `runs/check/cogito_person2-clips`. Chromium for most flows, WebKit for the 960 and 400 flows. Sizes 1920 x 1080, 1440 x 900, 960 x 1080, 400 wide, light and dark. No page errors in any run.

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
