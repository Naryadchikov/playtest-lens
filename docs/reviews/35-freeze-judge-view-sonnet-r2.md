Reviewer: Claude Sonnet 5.5 (high effort), Claude Code via T3, fresh reviewer, round 2. Task: docs/tasks/39-freeze-review.md, part B, "what a judge sees". Base commit 763f102 (README as of that commit, site files in `runs/demo-site/site/` as served on `http://127.0.0.1:8765/`). Round 1 is docs/reviews/34-freeze-judge-view-sonnet.md.

I read README.md as a judge would, opened the four pages and the front page in Chromium and WebKit through Playwright (1920 x 1080 dark, 1440 x 900 light, 390 px dark and light; throwaway contexts), opened Watch from the first top problem on Player 1 at three sizes in both engines, and went through the new GIF with ffmpeg. Captures: `/tmp/t39r2/` (pages `*-first.png`, Watch `*-watch-prob1.png`, GIF frames and sheet `/tmp/t39r2/gif/`), scripts `/tmp/t39r2/s/`. Nothing was copied into the repo.

## Score: 8.6 / 10, PASS (bar is 8.5)

| Part | Score | One line |
|---|---|---|
| README | 8.6 | The first screen now carries problem, solution, the Meta-model case and the held-out result; the demo video is still absent (known) |
| Demo site | 9.0 | Front page now shows the product; no errors, no overflow, clips play in both engines |
| GIF | 8.2 | Shorter, starts on the good moment, under 5 MB; text is still tiny and it ends before the payoff |
| Overall | 8.6 | Weighted by the rubric (Impact 30, Meta tooling 25, Technical depth 20, Demo 25), leaning on the first minutes |

The margin over the bar is thin, and the open video link (known, out of scope for the score) is what keeps the Demo weight from scoring higher.

## Round 1 findings, one by one

| # | Round 1 finding | Now | Evidence |
|---|---|---|---|
| 1 | README and front page promise three playtests, demo shows two | Fixed | README line 9: "two real playtests of the same level"; line 33: the developer's run is "in the numbers only, not on the demo site". Front page text and meta description say "Two real playtests" (`runs/demo-site/site/index.html`). Three cards/pages for two players still match. |
| 2 | Demo video is a hidden placeholder | Open, known | README line 13 is still an HTML comment. Out of scope for the score per the brief. |
| 3 | GIF does not show the product at its best | Mostly fixed | `report.gif` is now 15.6 s, 960 x 600, 156 frames, 10 fps, 4.9 MB (was 21 s, 6.8 MB). It opens on the Read page for about 2 s, then Watch on moment 4 with the quote visible (`/tmp/t39r2/gif/f4.png`, the better clip frame: Archive door and keypad), then Play the session. Residual points are finding 2 below. |
| 4 | Meta-model case sits in the middle | Fixed | README line 7 now says Spark takes 2-minute windows "as video with its sound in one request", so "no frame sampling and no separate speech model", and about $0.18 for 21 minutes. Both on the first screen. |
| 5 | Best evidence comes after the how-it-works list | Fixed (enough) | README line 7, second sentence: "On a playtest nothing was tuned on, it found the places where the developer saw the player slowed, flagged a possible bug, and rated the friction higher than he did." It names found, bonus and overrated. The "missed" part is only in the section below, which is honest enough for a one-liner. |
| 6 | README links dead until public | Open, known | Out of scope per the brief. Check with README open in a logged-out window after the switch. |
| 7 | Tab titles identical for Spark and Open | Fixed | `<title>` now reads "...session lobby-player-1, Muse Spark 1.2" and "...Muse Spark Open (open weights)". The on-page heading still shows the slug "Playtest lobby-player-1" (`/tmp/t39r2/gif/f0.png`), see nit 5. |
| 8 | Front page has no picture, no social preview | Fixed | The front page shows a Watch screenshot above the cards at 1440 and 390 (`chromium-index-1440x900-light-first.png`, `webkit-index-390-dark-first.png`). `og:image`, `og:title`, `og:description`, `twitter:card` are present; `preview.jpg` is 111 KB. The other three pages still have no `og:image` (grep count 0), which only matters if a judge shares a report link. |
| 9 | "held out" tag unclear | Fixed | The Player 2 tag reads "not used for tuning". The README tables still say "(held out)", which is fine next to the explanation under them. |
| 10 | "has to prove" overstates independence | Not fixed, one place fixed | Line 5 now says "has to check". Line 58 still says "the second one has to prove each claim". Wording is Sasha's call; see nit 2. |
| 11 | README length, order is the issue | Fixed by 4 and 5 | The first screen (lines 1 to 11) now holds everything. The length is unchanged and fine. |
| 12 | Open page ranks differently from the README's Player 1 paragraph | Fixed | README line 45 now says "The Spark page puts it first". |

## Findings now

### Blocking

None.

### Should fix

1. **The demo video is still the one piece missing from the rubric's Demo 25%.** Known, listed only so it is tracked: put the link directly under the GIF when it exists (README line 13).
2. **The GIF is better but its text is tiny and it stops before the payoff.** At 960 px wide the quote and the cause read at about 14 px (`f4.png`); inside the README column (about 800 px) they will be smaller. The Play the session half (frames at 9 to 15 s) shows the clock counting to 1:03 with "Up next: moment 4 at 3:52", then loops; it never reaches the stop at an unplanned moment, which is the feature's point, and moment 4 was just shown before it. Suggestions, Sasha's call: show Play first, let it run to the stop and the clip, drop the separate static Watch segment, or crop to the clip, quote and map so the text is larger. Not blocking: a judge who watches 15 s still sees clip, quote, cause and map.

### Nit

1. README line 7 is dense: one long second paragraph carries the model, the cost, the held-out result. It reads fine; if Sasha wants it lighter, split the held-out sentence off.
2. README line 58 still says "has to prove". The evidence it cites carries the claim; "checks against" would match line 5. Both passes are the same model, which the README states.
3. Watch clips autoplay muted (the speaker icon is struck through in `f4.png`), while the front page says "The clips carry the players' voices". A judge hears nothing until they unmute. The quote is shown as text, so nothing is lost; a one-line "unmute for the player's voice" hint would help.
4. Reports 1 (Open) and 2 have no `og:image`; only the front page does.
5. The report's first screen heading is the file slug, "Playtest lobby-player-1" (`f0.png`, `chromium-lobby-player-1-1440x900-light-first.png`). "Player 1, Muse Spark" would read better.
6. The front page links read "Open the report" for both players, and the second link for Player 1 reads "Same session, open-weights model". Clear enough in the capture; at 390 px the second link is below the first screen (`webkit-index-390-dark-first.png`).

## Demo site check

| Page | 1920 dark | 1440 light | 390 px | Horizontal overflow | Console and page errors |
|---|---|---|---|---|---|
| index.html | ok | ok | ok (page is 1546 px tall) | none | none |
| lobby-player-1.html | ok | ok | ok, about 14,990 px | none | none |
| lobby-player-1-open.html | ok | ok | ok, about 22,870 px | none | none |
| lobby-player-2.html | ok | ok | ok, about 6,690 px | none | none |

- 32 page/size/engine combinations, zero horizontal overflow, zero console or page errors. The only `requestfailed` events are `.mp4` still-frame loads aborted by the browser on page close, same as round 1; every clip I opened played.
- Watch from "Archive, Code Lock" (Player 1): in both engines at 1920, 1440 and 390 the clip loaded (readyState 4) and `currentTime` advanced from about 1.3 to 3.8 s in 2.5 s. Load time 0.18 to 0.43 s locally.
- The page was not re-judged beyond this; nothing in the first minutes hurts a judge.

## What I did not check

- Real-network behaviour and the size of the site on GitHub Pages: the local server ignores byte ranges, and the site is 404 MB (the 400 MB figure is large for Pages, check its limits and a cold load after publishing).
- The Play the session run live in the browser (judged from the GIF), keyboard or screen reader use, audio, Safari on a real device.
- Any number in the README tables, the demo video (not present), the live GitHub Pages URL and the GIF URL (dead until public, known).
- Files other than README.md and the demo site (part A is Grok's).
