# Status

The orchestrator keeps this file up to date at each milestone and at the end of each day, so a fresh thread can pick up from it (AGENTS.md, "Saving Claude usage"). Keep it under a page.

## Roles (Sasha, 2026-10-31)

Claude Opus 5.5 orchestrates and writes the code. Claude Fable 5.1 designs the report when Sasha asks. A fresh Grok 4.7 xhigh through Cursor reviews code; a fresh Claude Sonnet 5.5 judges captures, the UX and the README, and takes the code review when Cursor's limits stop Grok. Effort high for every Claude agent, xhigh for Grok. The Meta pool is for the product's video and audio only. Table: AGENTS.md.

## Where things stand (2026-11-03)

- **Frozen:** no more tuning since 2026-11-01. The check prompt is v2 with the friction guard. The freeze review passed (Grok, the repo: PASS; Sonnet, the judge view: 8.6 PASS), docs/tasks/39-freeze-review.md.
- **Three playtests, all consented:** Player 1 (21:21, the demo), Player 2 (6:04, held out), and the developer's own run (8:32). Findings and pages in both modes, under readable names in `runs/demo/` (git-ignored).
- **The demo site** is staged in `runs/demo-site/site/` and pushed to `Naryadchikov/playtest-lens-demo`, private, Pages off until the green light.
- **The repo is ready to go public:** DECISIONS.md is out of the history and kept locally only; the testers are Player 1 and Player 2 everywhere; a fresh recursive clone passes the offline tests (249). docs/PUBLIC_CHECKLIST.md steps 1 and 3 to 9 are done; step 2 waits for the video link. The step 4 scans and the tests passed on `a309388` on 2026-11-03 (review 37, PASS).
- **Submission:** the form's fields and the drafts for its text are in docs/SUBMISSION.md.

## Next (Sasha's target: submit by 18:00 CET on Wed 4 Nov; the deadline is 03:00 CET on Thu 5 Nov)

1. Sasha records and edits the video (docs/VIDEO_PLAN.md) and sends the YouTube link. It goes under the GIF in the README and on the site's front page.
2. Sasha asks both testers about Meta's promotion rights (the form's permission box) and Spark contributor training.
3. The green light, on Sasha's word: both repos public, Pages on, a signed-out check of the README GIF, the site and the clips (PUBLIC_CHECKLIST steps 10 and 11).
4. The X post, then the submission (the form needs the public repo URL and the video link).

## Credits used

`runs/costs.jsonl` sums to $30.40 (2026-11-01, unchanged since). The Meta pool figure of about $23.90 left was Sasha's, on 2026-10-28, not rechecked against Meta's dashboard.
