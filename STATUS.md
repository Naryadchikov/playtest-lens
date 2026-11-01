# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-31, DECISIONS.md)

Claude Opus 5.5 orchestrates and writes the code. Claude Fable 5.1 designs and builds the report when Sasha asks for it. A fresh Grok 4.7 xhigh through Cursor reviews code; a fresh Claude Sonnet 5.5 judges captures, the UX and the README. Muse Wonder is not called. The Meta pool is for the product's video and audio only. Normal mode: Contributor Spark 1.2. Open mode: Muse Spark Open on Baseten. Table: AGENTS.md.

## Where things stand (2026-11-01, evening)

- **The report** is the mix Sasha picked (task 37, Fable; fixes in task 38 and by Opus): Read (the verdict, top problems beside the map, every moment with a still under its place heading, the dropped candidates) and Watch (the clip about two thirds with the quote as headline, the summary and "Likely cause"; the map with the place line and the 30 s trail; Play stops only at unplanned moments; "Up next" while walking; Back to where you came from). It holds from 360 px to 1920 px. UX loop: 7.4, 8.6, 8.4, then **8.9 PASS** (review 29); code PASS (reviews 25 and 30). A half-screen rearrangement was tried and reverted (review 31). Latest `f397f7e`.
- **The check prompt** is v2 with the friction guard (`6c4953c`), one prompt for both modes. Final findings and pages for both sessions in both modes: `runs/final/` (from the cache, $0).
- **Staged, not published, not committed** (his words: nothing is published while we iterate): the demo site `runs/demo-site/site/` (his session, `index.html` Spark and `open.html` Open, the new layout); the README GIF `runs/demo-site/report.gif` (20 s, 960 px, 8.8 MB, his session). The old layout's copies are kept beside them (`*-old-layout*`).
- **The Godot add-on** in `godot/addons/playtest_lens/` with the map tool and a test project; the fork keeps the COGITO adapter and a checked copy.
- **One command:** `tools/run-analyzer.sh analyzer/analyze.py <recording> --log <jsonl>`.
- **Tester kit:** `runs/tester-build/PlaytestLens-Cogito-Windows.zip`; needs his task line and one Windows run.

## Remind Sasha

- Before testers get the build: the consent text says Meta may train on contributor-mode recordings; a tester who objects gets `muse-spark-1.2`. Sasha, 2026-10-28: "add it for now, and remind me about it once we do testing."

## Open questions for Sasha (asked 2026-11-01, evening)

1. The 21 changed cards on `runs/check/prompt33/guard-judge.html` (before and now side by side), and whether the yellow "Cutscene Trigger" box at 5:17 in her session is meant to be visible.
2. Her consent: may her session be public (README numbers, video, her voice in the clips)?
3. Testers: send the kit (his task line, one Windows run) or ship on the two sessions.
4. Words on the page (proposals): "Analyzed with {model}." and whether the model needs a clearer tag; the page title "Session cogito"; the raw volume name "CUBICLE_AREA" in his session.
5. Publish: the demo site on GitHub Pages (new public repo) and the GIF in the README, now that the layout is done.

## Next

1. His answers above; then: README final (numbers from `runs/final/`, the GIF, the card check), the marking page for the final cards, VIDEO_PLAN for the new layout, the X clip.
2. Tue 3 Nov: freeze review (Grok on the whole repo, Sonnet on README and captures); he records the video.
3. Wed 4 Nov: PUBLIC_CHECKLIST (DECISIONS.md removed with no history, scans), repo public, Pages live, submit by 18:00 CET (deadline 9:00 PM Eastern), X post.

## Credits used

`runs/costs.jsonl` sums to $29.27 on 2026-11-01: Meta pool $14.78, Baseten $14.49. The Meta pool figure of about $23.90 left was his, on 2026-10-28, not rechecked against Meta's dashboard.
