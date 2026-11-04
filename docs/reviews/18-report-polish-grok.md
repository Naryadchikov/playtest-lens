Reviewer: Grok 4.7 (xhigh) through Cursor, in T3 Code. Commit b36e564.

PASS

## Blocking

None.

## Nits

1. `report/render.py:1241` (the label is `report/render.py:111`). Class: a same-second span still prints both ends on an attempt heading.
   `_span` (`report/render.py:401`) returns one m:ss when both ends format the same. The card head (`report/render.py:1055`) and the group notes (`report/render.py:1212`, `report/render.py:1218`) call it. The attempt heading fills `Attempt {n} ({start}-{end})` with two `_mss` calls.
   Input: `tests/fixtures/findings_redesign.json`, the first kept finding, `time_s` 39.2, `end_s` 39.8, `attempt_start_s` 39.2, `attempt_end_s` 39.8.
   Result: the card time is `0:39 (0 s)`, the group note is `1 attempt, 1 moment, 0:39`, and the heading is `Attempt 2 (0:39-0:39)`.
   On the Player 1 page the attempt headings are real ranges: 3:41-3:53, 14:20-14:47, 19:16-19:42, 9:39-10:20.

2. `docs/design/DESIGN_NOTES.md:18`. Class: the markup note places the clip in two spots.
   The sentence says the card's children are `.card-body`, then the clip, and the body-children list ends with `.clip` as well. In `report/render.py:1095` the clip is the next sibling of `.card-body`. The wide layout is `.card:has(> .clip)`, so a clip placed inside the body would stay under the text.

## What held

`.venv/bin/python -m pytest -q`: 193 passed, exit code 0, 40.52s. No model call. The transcribe tests use a mock HTTP transport.

Rendered `runs/check/lobby-player-1-findings.json` to `/tmp/review18.html`. Against a render from `c10fbc2`, the visible text differs only in four group notes: `0:39-0:39` to `0:39`, `5:17-5:17` to `5:17`, `5:27-5:27` to `5:27`, `8:59-8:59` to `8:59`. `LABELS` is the same. `tile zero` matches the kinds whose count in the file is 0.

Three kept findings from `random.Random(18)`: f6 at 255.0 s (4:15), f4 at 232.0 s (3:52), f29 at 1204.0 s (20:04). Summary, quote, checker note, and time in each card match the file. Every kept string that contains `&`, `<`, `>`, or a quote is escaped in its card.

Firefox 159 on that page. The svg box matches the img box. A start point, an end point, and a pin sit on the image (error 0, and 0.01 px at the narrowest width) at inner sizes 1440x1015, 1440x715, 1440x567, 700x815, 844x347, and 500x759. At inner height 567 the image is 255 by 391 px, under the 480 px column cap, and the error is still 0. With `.map { max-width: 300px }` the image is 298 px wide and the error is 0. Heat checked: `.heat` is `inline`, the trail and the timeline are `none`, the image filter is grayscale. The clip sits to the right of the text at inner width 900 and under the text at 899. The map column is one track at inner width 760 and two tracks at 761. The start label is above the circle, inside the viewBox, and clear of the circle. The inline script has run: the timeline is shown, no card is dim, and both route polylines are still there. `.card[data-t]`, `.pinlist [data-t]`, `details.puzzle`, and `polyline[data-t]` still match with the card-body wrapper. Every kept clip is a sibling of `.card-body`.

The diff is the three named files. No key, no recording, no em dash, no en dash.

## What I did not check

I did not judge the look. I did not open Safari or Chrome. I did not run a print preview, so `@media print` was never the active medium. I did not drag the time slider. I did not read held-out notes or watch the recording. I did not call the Meta API or read `runs/costs.jsonl`. I did not touch `game/`.

Pre-existing, outside this diff: the print rule `.clip { display: none }` is one class, and `.clip.video { display: block }` is two, so the print rule does not hide the video element.

## Orchestrator's follow-up (Claude Opus 5.5, Claude Code in T3 Code)

- Nit 1 fixed: the attempt heading now uses `_span` (`LABELS["moments"]["attempt"]` is `Attempt {n} ({span})`). The Player 1 headings read the same.
- Nit 2 fixed: DESIGN_NOTES.md now says the clip is the body's next sibling.
- The print finding is pre-existing and went to docs/FOLLOWUPS.md.
