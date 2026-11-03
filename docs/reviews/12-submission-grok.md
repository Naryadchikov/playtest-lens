# Submission review

Reviewer: Grok 4.7, Cursor. Fresh reviewer. I did not build this project. Commit: `3c5c920` (2026-10-28, "Add a time trail and a separate heat map on the report"). Judged 2026-10-29, six days before the 2026-11-04 9:00 PM Eastern deadline.

Read: README.md, PLAN.md, STATUS.md, docs/THIRD_PARTY.md, docs/PUBLIC_CHECKLIST.md, the analyzer pipeline and `report/render.py`, docs/reviews/11-report-timeline-sonnet.md, docs/tasks/26-open-model-grok.md, docs/tasks/26-open-model-opus.md. Pages: `runs/check/cogito-report-26.html` (contributor Spark) and `runs/check/cogito-report-open.html` (Muse Spark Open). Both are git-ignored and were rendered after that commit.

I did not play COGITO, watch a recording, open a clip, or read notes held out for the score. No API call. This is a hackathon judge's read of the package, not a PASS or NOT PASS code review.

## The problem, and whether this package is competitive

Watching playtest footage takes hours, so small teams skip it. Playtest Lens is meant to watch the screen and the player's voice, line that up with the game's event log, and return the moments where someone got confused, stuck, or surprised, after a second model call that can throw a moment out.

That is a real problem, and the package is past a demo wrapper. On one 8:32 COGITO session it produces two full reports: clips, quotes, a checker note, a route, a heat map, and a list of drops. Muse Spark 1.2 contributor, Voice Transcribe, and Muse Spark Open on Baseten are all in the path. For Meta's rubric that is a strong tooling and engineering entry, and a credible open-weights entry.

It is not yet a competitive submission. The README still says how to run it will come later. There is no public repo, no three-minute video, no second player, and no score against blind notes. The first screen of the report says the player lost 0:00. A judge who only has the repo today cannot grade the product the plan describes.

Weights used below are the ones the participant guide states, as copied in docs/PUBLIC_CHECKLIST.md: Impact 30%, use of Meta's models 25%, technical depth 20%, demo 25%. Stage one is pass or fail on theme fit and real use of Meta's models. I am not inventing point scores.

## What is strong

- The pipeline is one path. Spark (or Spark Open) proposes moments, the event log can add its own, a second call on a short clip keeps or drops each one, and `findings.json` is what the page renders. `report/render.py` formats that file. It does not decide a finding, a time, or a count. Dropped moments stay on the page with a reason. On the contributor page that is 20 kept and 11 dropped, out of 31. On the open page it is 18 kept and 18 dropped, out of 36. The drop reasons argue from the transcript and the clip. That is the part a judge can recognize as more than a summary.
- The contributor page is a thing you can show. Session `cogito.mp4`, 8:32, start flash at 25.2 s. Each kept card has a `<video>` pointing at a local clip (20 clips). The map has a 464-point route, pins, a time trail, and a heat view. The heat spots in the file are 2:12, 0:25, and 0:15. A previous review (docs/reviews/11-report-timeline-sonnet.md) drove the trail in a browser: a 15 s window lit one pin and dimmed the other cards, and the heat view hid the route. I did not repeat that browser pass.
- Open-weights mode recovered. The task 26 notes are right about the empty run: eight silent frames across 120 s, no clock, and a prompt that allows `[]`. The current open page is a second full report on the same session, checker model `meta-models/muse-spark-open-1026`, same lobby map. Of the 20 contributor keeps, 14 have an open keep within 15 s, and 11 within 8 s. The code path now labels each frame and puts the Voice Transcribe text in the prompt. That is a real second mode, which is what the open-weights bonus asks for (partner inference counts).
- A second game has already been through the checker. The Talos findings file is about 15.5 minutes, with no event log and no map: contributor Spark kept 22 and dropped 13. I did not judge whether those moments are right. It does show the pipeline is not hardcoded to one COGITO report.
- Prior work is in better shape than most hackathon repos. docs/THIRD_PARTY.md separates COGITO, Godot, fonts, and sounds from the analyzer, the report, and the logger. A judge who checks "new work only" can see the line. The license line is a name, not a placeholder.

## What is weak

- Impact is unproved. Both pages are one session, and the player is the author. `cross_player` only emits a group when two sessions share a place, so neither page has an Across players section. There is no score against blind notes. PLAN.md treats his own recordings as the tuning set, so a score computed on this COGITO file would not be the proof the plan describes. The rubric's heaviest weight sits on this gap.
- The glance row says `0:00 of 8:32` under "Time lost to being stuck or confused," next to 12 stuck or confused keeps. Every live finding has `end_s` null, and `analyzer/spatial.py` only sums spans that have an end. The tile is the second thing on the page. It reads as a broken headline.
- The contributor bug cards name the wrong engine. At 8:16 and 8:22 the summaries and the checker notes say the Unity editor, Unity, and a C# script. The open page, about four seconds earlier and later, says a Godot debug overlay and an out-of-bounds fall. The game in this repo is Godot. I did not watch the clip, so I cannot say which pixels are on screen. I can say the two models disagree, and the contributor text is not safe to put in a video.
- Twenty keeps in eight and a half minutes is a feed. The torn-page and keypad stretch (about 4:51 through 6:16 on the contributor page) is many cards of one search, under area names that do not match: Office Complex, Archive code hunt, CEO Office Complex, Office Area, Cubicle Office Area. A designer still has to do the grouping the tool was supposed to do. Surprises that read as designed delight (the hidden room, the real laptop) sit in the same list as unplanned stuck.
- Seven cards on each page are tagged `planned challenge?`, question mark included. That string is the friction label in `report/render.py`. It looks unfinished, because it is: STATUS.md still calls the wording a proposal.
- Quotes are often hard to read (repeated words, broken phrasing). The sentence above each quote is fluent. A judge comparing them will trust the page less, even when the checker is careful. Voice Transcribe is doing what it did; the page shows the raw result.
- Open mode does not receive the recording. It receives up to eight frames, time labels, and transcript text. Contributor Spark receives the video. The bonus still fits. A video that says Spark Open "watched the session" the same way would be a false claim, and `analyzer/client.py` is short enough for a judge to check.
- The map is one top-down of the lobby scene. Follow-ups already note that an upper floor (the CEO office) is drawn on that same slice. I did not measure pin error.
- The front door is stale. README.md says the run steps come once it runs, and it lists Muse Wonder as a builder. Wonder is not the product's model. STATUS.md still says the first COGITO video is not here. The pages exist.

## Winning chances

Assumptions: I have not seen the footage, so "the findings are true" is not something I can grant. I do not know how many teams will submit, so these are bands, not percents. The package is judged as of 2026-10-29 morning. Six days remain. Nothing below is a score on the rubric.

- As it sits (private repo, no video, README unfinished): there is no submission. Stage one cannot be awarded from a private tree.
- Video, public repo, and a README, with this same single session and these pages: stage one is a likely pass. The theme fits an indie developer, and the models are used on a real session for more than a single prompt. Main prize: unlikely. I would expect it to lose on Impact and on the demo to teams who show another person and a number. Open-weights bonus: a real entry, and a better chance than the main prize, because two full reports already exist. A win there is possible, not something I would call likely, and it depends on who else shipped Spark Open as a product. Best Agentic is a weak fit: the check is a second call with evidence, which is a pipeline. Community vote and viral need a public post that does not exist.
- If, before the freeze, there is one outside tester, a blind score on a session the prompts were not tuned on, the 0:00 tile and the Unity card are gone from what judges see, and the video is the report (one stuck moment, one drop, the map, then both models): a shortlist is a reasonable hope. A win moves into the plausible band only if that score is strong and the misses are shown. I have not seen that evidence, so the package is not in that band today.

The guide's anti-examples include a simple image analyzer. The risky cut is the open-weights mode alone, because it is frames. The video has to show the recording, the voice, and the log in the first minute, with COGITO named as the prior-work test bed.

## Must fix to submit

These are the rules and the trust failures. The rest can slip and the entry can still be filed.

1. A public repo, a reachable three-minute video, and a README a stranger can follow. The video shows only work from the event, names COGITO as prior work, and shows video, voice, and the event log. Replace "How to run it comes here once it runs" with the real commands, the two model modes, and the video link. Drop Muse Wonder from the builder line.
2. docs/PUBLIC_CHECKLIST.md, on the exact commit: secret scan, no recordings in git, `DECISIONS.md` out of history before the visibility flip, and the Discord question on the planning commit that landed after kickoff but before the building period, if that question is still open. Tester media stays out. The clips next to the HTML (58 files) must not be committed.
3. Do not put the contributor bug card in the video while it says Unity. Use a card a human has watched, or the open page's Godot account after that same check. A false engine name on the climax is a trust failure, and it is the kind of mistake a judge remembers.

## Moves the score before the deadline

In order. Each one changes what a judge believes. None of them is a new feature.

1. The blind score, on a held-out tester, shown as hits and misses. This is the Impact proof and the 2:00 beat in PLAN.md. A score on this COGITO session does not count: that file is the session the report was built against.
2. Record the video from the page, not from the architecture. One stuck moment with clip, quote, and log. One drop, read aloud. The heat spot of 2:12. Then the open page beside it, with one sentence on what Open actually received (labeled frames and the transcript, after a silent-frame run returned `[]`). Say that 14 of 20 contributor keeps have a nearby open keep. That comparison is the bonus entry.
3. The first screen. Hide the time-lost tile until `end_s` is filled, or fill the spans. Replace `planned challenge?` with a finished word. A judge reads the glance row before any clip.
4. Collapse the torn-page and keypad stretch into one problem with a stable area name. Twenty cards in one short session reads as recall without judgment. The check already drops routine play. The kept list needs the same restraint.

## Nice

Leave these if the four items above are in doubt.

- One command that runs candidate, check, beats, map, and render. The modules are already the one path. A judge should not have to discover the order.
- A second map slice for the upper floor, so CEO-office pins are not drawn on the lobby plan.
- Shorter quotes, cut to the sentence the checker relied on. The transcript model will stay rough.
- The trail nits from review 11: the start marker stays on the map inside a short window, and the view switch depends on `:has`. Fine for the browsers you will record.
- Aiming the copy at the agentic bonus. The check is the agentic part you have. Writing a longer agent for the prize would spend the week on the wrong gap.

## What I did not check

I did not re-run the suite. Review 11 recorded 180 passed and 2 failed, then a one-line test fix for the heat gradient. I did not open the browser, play a clip, or confirm that a pin sits on the right room. I did not read Talos moment by moment. I did not audit `game/` beyond THIRD_PARTY.md. Finding quality against the designer's own memory is Sasha's call: I cannot make it.
