Reviewer: Claude Sonnet 5.5 (high effort), Claude Code via T3, fresh reviewer. Task: docs/tasks/39-freeze-review.md, part B, "what a judge sees". Base commit 974a1b2 (README as of that commit, site files in `runs/demo-site/site/` as served on `http://127.0.0.1:8765/`).

I read README.md as a judge would, opened the four pages in Chromium and WebKit through Playwright (1920 x 1080 dark, 1440 x 900 light, 390 px dark and light; throwaway contexts), opened Watch from the first top problem on Player 1 at three sizes in both engines, and went through the GIF frame by frame with ffmpeg. Captures: `/tmp/t39/` (page captures `*-first.png`, Watch captures `*-watch-prob1.png`, GIF frames `/tmp/t39/gif/`), scripts `/tmp/t39/s/`. Nothing was copied into the repo.

## Score: 8.3 / 10, NOT PASS (bar is 8.5)

| Part | Score | One line |
|---|---|---|
| README | 8.0 | Problem and solution land fast; the Meta-model case and the best evidence sit too low, and it promises three playtests the demo does not show |
| Demo site | 8.8 | Loads clean, no errors, no overflow, clips play in both engines; Watch is the strongest minute; the front page is text only |
| GIF | 7.5 | Readable, loops, but a 3 s static start and a weak clip frame; it does not show the product at its best |
| Overall | 8.3 | Weighted by the rubric (Impact 30, Meta tooling 25, Technical depth 20, Demo 25), leaning on the first minutes |

The gap to 8.5 is small and all of it is cheap: findings 1, 2 and 3 below. I found no wrong data and no broken page.

## Findings

### Blocking (for PASS)

None that break the product. The two below are the ones that cost the score.

### Should fix

1. **README and the front page promise three playtests; the demo shows two.** README.md line 9: "three real playtests of the same level, no install", and the table and the "On three real playtests" section include the developer's own run (8:32). The front page meta description says "Three real playtests" (`runs/demo-site/site/index.html`, `<meta name="description">`). The front page has two cards (Player 1 with a second link for Open, Player 2) and three report pages in total, none of them the developer's. A judge who counts will find three pages for two players, or two players for "three playtests", and will wonder where the third is. Fix with Sasha's words: either add the developer's page to the site (he consented, STATUS.md line 12), or say "three reports, two players" and mark the developer's run as numbers only. Evidence: `/tmp/t39/chromium-index-1920x1080-dark-first.png`.
2. **The demo video is a hidden placeholder.** README.md line 13 is an HTML comment, `<!-- Demo video: the link goes here once it is uploaded. -->`. Demo is 25% of the rubric and the README is the first thing a judge opens. Until the link exists the README has no video, and the GIF is the whole demo (see 3). Put the video link directly under the GIF, or under the live-demo link, as soon as it exists. This is a known open item; I list it because it moves the score.
3. **The GIF does not show the product at its best.** `report.gif` is 21.0 s, 960 x 600, 252 frames, 12 fps, 6.8 MB, loops. What I saw frame by frame (`/tmp/t39/gif/sheet.png`, `f5.png`, `f15.png`):
   - 0 to 3 s: the Read page, static. A judge sees nothing move for the first seconds.
   - 3 to 9 s: Watch on moment 21 of 24, "I still still don't know what is the code". The clip frame is a close-up of a wall and shadow (`f5.png`); the player's words and cause read well, but the picture says nothing about the game or the problem. The README caption calls this "the top problem, its clip", but it is the last moment of that problem.
   - 9 to 21 s: Play the session, 10x. The clock, "Up next: moment 4 at 3:52" and the map with the trail read well (`f15.png`), but for 12 of 21 seconds only the clock and the map trail change.
   - All text is 10 to 13 px at 960 px wide, so in the README column (about 800 px) the quote and the cause are hard to read.
   Suggestions (Sasha's call): start on Watch with the quote visible in the first second, pick a moment whose clip shows the player at the lock (moment 4, frame in `chromium-p1-1440x900-light-watch-prob1.png`, is a better picture than 21), and cut the idle second half of Play. Keep it under 15 s and under 5 MB.
4. **The Meta-model case is in the middle of the README.** "Use of Meta's models" starts around line 59 and says what each model does, not why Meta's models make this possible. Two facts a judge will want sooner and that are already in the README: Spark takes the video with its sound in one request (no frame sampling or separate vision model), and a 21-minute session costs about $0.18 (Spark) or $2.30 (Open); both are in the table at line 38, not in the first screen. One sentence under the second paragraph would carry 25% of the rubric.
5. **The best evidence comes after the how-it-works list.** The held-out comparison (found, bonus, overrated, missed; README lines 44 to 49) is the most credible thing in the README and the strongest Impact argument, including the honest "Overrated" and "Missed" lines. It starts at line 40. A one-line result near the top ("On a session nobody tuned on, it found the three places the developer saw, one possible bug, and overrated the friction") would give a skimming judge the point without scrolling.
6. **README links are dead until the site is public.** `https://naryadchikov.github.io/playtest-lens-demo/` and the GIF URL (README.md lines 11 and 13) point at the private repo with Pages off (STATUS.md line 14). Today the GIF renders as a broken image in the README. Expected, and the public checklist covers it; I flag it so it is checked after the switch, with the README open in a logged-out window.

### Nit

7. Page titles and headings use the file slug, "Playtest lobby-player-1" (`<title>Playtest Lens: session lobby-player-1`). The Spark and Open pages for Player 1 have the same tab title, so two tabs look identical. "Player 1, Muse Spark" and "Player 1, Muse Spark Open" would read better. First screen: `/tmp/t39/chromium-lobby-player-1-open-1440x900-light-first.png`.
8. The front page has no picture. It is clean and the primary button is obvious, but a judge who clicks nothing sees only text. A small crop of a report (or the GIF) in the first card would show the product before the click. No Open Graph image or social preview tags either (`grep -c og:image` is 0 on all four pages), so a shared link has no thumbnail.
9. The tag "held out" on the front page is explained in the card text for Player 2, but a judge from outside ML may read it as "withheld". "Not used for tuning" is clearer. Wording is Sasha's call.
10. README line 5 and the "Use of Meta's models" list say one Spark pass proves another; both passes are the same model. The README says so itself, which is honest, but "has to prove" can read as stronger independence than there is. The evidence it cites (clip, words, log) carries the claim; consider "checks against" instead of "proves".
11. README length: 93 lines, about 1,250 words. The first 30 seconds are good (lines 1 to 13). The sections on the add-on, how it was built and built-with are fine for a judge who keeps reading. No cut needed; the order is the issue (4 and 5).
12. The open-weights page for Player 1 ranks "Break Room, Resolved" first and the Archive code lock second (`chromium-lobby-player-1-open-1440x900-light-first.png`), while the README's Player 1 paragraph says the page puts the code lock first. True for the Spark page, which that paragraph is about, but a judge who opens the Open link right after reading it will see a different order. Say "the Spark page" in that sentence.

## Part 1: README, in 30 seconds

Lines 1 to 9 carry the problem (watching a playtest takes as long as the playtest, small teams skip it, the room's builder never sees the lost moment) and the solution (Spark watches, a second pass proves each moment, one page with map, clip and words). A game developer gets it. The "Watch / Read" description, "by design" against "unplanned", and the dropped-moments list are clear and distinctive. The held-out section is the best-written part and its honesty (overrated, missed, can't see) helps Impact and Technical depth. No overclaim found beyond nit 10; the cost and the "agreed on 17 of 21" lines are specific and checkable by the orchestrator (I did not check the numbers, as the brief says).

## Part 2: demo site

| Page | Chromium 1920 dark | Chromium/WebKit 1440 light | 390 px | Horizontal overflow | Console and page errors |
|---|---|---|---|---|---|
| index.html | ok | ok | ok (`webkit-index-390-dark-first.png`) | none | none |
| lobby-player-1.html | ok (first screen holds title, model, headline, top problems, map) | ok | ok, one long scroll (about 15,000 px) | none | none |
| lobby-player-1-open.html | ok | ok | ok, about 22,900 px long | none | none |
| lobby-player-2.html | ok | ok | ok, about 6,700 px | none | none |

- Local load time, 0.18 to 0.27 s per page (Chromium and WebKit). No console error or page error in either engine at any size.
- Watch from "Archive, Code Lock" (Player 1): the clip loads and autoplays muted in Chromium and WebKit at 1920, 1440 and 390 (readyState 4, currentTime advancing from 1.3 s to 3.8 s over 2.5 s). Captions, quote headline, cause, map with pin and trail, "Before this moment" and the timeline are all in view at 1920 and 1440 without scrolling (`webkit-p1-1920x1080-dark-watch-prob1.png`, `chromium-p1-1440x900-light-watch-prob1.png`). At 390 the clip, quote, summary and cause stack in order and the map is one scroll away (`webkit-p1-390-dark-watch-prob1.png`).
- Light and dark both hold. The first screen at 390 px shows the title, the headline and the first problems (`webkit-lobby-player-1-390-dark-first.png`).
- Player 2's first screen shows "Archive" and "Archive, Code Lock" as separate top problems (`webkit-lobby-player-2-1440x900-light-first.png`). Clear enough; I note it only because a judge may read them as duplicates.
- Chromium's `requestfailed` events for `.mp4` in my first sweep were the browser aborting still-frame loads when I closed each page, not missing files; every clip I opened played.

The page design is not re-judged beyond this: nothing in the first minutes hurts a judge (review 29, 8.9, still holds).

## What I did not check

- Real-network behaviour. The local server (`python -m http.server`) ignores byte ranges, so my byte counts (about 64 MB of clips fetched on Player 1's page load, 118 MB on its Open page, 33 MB on Player 2) are not what GitHub Pages will send. The pages use `preload="metadata"` on about 72 `<video>` stills; on a real host with range support this should be small, but I did not measure it. The whole site is 401 MB, with Player 1's clips at 163 MB; check the Pages size limit and a cold load on a phone connection after publishing.
- The Play the session run in the browser (I judged the GIF, which shows it) and keyboard or screen reader use (covered in earlier reviews).
- Any number in the README tables, the demo video (not present), the live GitHub Pages URL (private), Safari on a real device, and audio (clips were muted for autoplay).
- Files in the repo other than the README (part A is Grok's).
