# 41: The final check before going public

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-03. Reviewer: a fresh Claude Sonnet 5.5 (high), independent of reviews 33 to 37. Read-only. Report in `docs/reviews/38-final-public-sonnet.md`. Rules for reviews: docs/REVIEW.md. Only a reviewer writes PASS.

Sasha's ask, T3 Code chat, 2026-11-03: "can you do final independed check with sonnet on high please, both repos, links, ording, everything, that we are 100% sure all is clean and ready to go public please"

## What goes public

1. `Naryadchikov/playtest-lens`: this checkout, `main` at the commit that adds this brief. A new private repo created on 2026-11-03 holding only the rewritten history; the old repo was renamed `playtest-lens-old-history` and stays private.
2. `Naryadchikov/playtest-lens-demo`: the GitHub Pages site, checked out at `runs/demo-site/site/` (its own git repo; the only part of `runs/` you may open). Pages turns on at the green light, at https://naryadchikov.github.io/playtest-lens-demo/.
3. `Naryadchikov/cogito-playtest-lens`: the fork, already public, the submodule at `game/`, our branch `playtest-lens`.

## Check

1. **Clean, all three repos, every commit that will be public** (`main` here, `main` in the demo repo, `676be6d..playtest-lens` in the fork): no keys or tokens, no personal emails, no home paths, no tester media outside the demo repo's clips, no `DECISIONS.md`, no word that says who a tester is to the author, nothing about the author's other projects or employer. Write your own scans. Do not write the words you searched for into your report: describe them.
2. **Links:** every link in README.md, docs/SUBMISSION.md, docs/PRIOR_WORK.md, the demo repo's README.md and `index.html`, and the report pages' outbound links. Relative links resolve to tracked files. GitHub URLs point at the right owner, repo, branch and path (`gh api` reads are allowed; the repos are private until the green light, so check the target exists through the API, not signed out). The README's GIF and the og image load from the Pages URL, so check that the file exists in the demo repo under that path.
3. **The demo site works:** serve `runs/demo-site/site/` on `127.0.0.1` with a server you start and stop yourself, and open the front page and the three reports in Chromium and WebKit (`PLAYWRIGHT_BROWSERS_PATH=0 .venv/bin/python -I <script>`; never `playwright install`): no console errors, no 404, every clip a report references exists and plays, links between pages work. Captures in `/tmp/t41/`.
4. **Wording:** README.md, the demo front page and docs/SUBMISSION.md read as one story: the same numbers (lengths, kept and dropped counts, costs, model names), the same names for the players, no claim the code does not back, no chat voice or internal notes a judge would trip on. Words are Sasha's call: propose, do not rewrite. No em dashes or spaced en dashes in public text.
5. **A fresh clone works:** `git clone --recursive` of this repo from GitHub into `/tmp`, then the offline tests with this checkout's `.venv` (`<checkout>/.venv/bin/python -m pytest -q`).
6. **Ready to flip:** the remote holds only `main` and no tags, local `main` equals it, the fork's `playtest-lens` equals its remote, and docs/PUBLIC_CHECKLIST.md's remaining steps (10 to 12) are right and complete.

## Rules

Read-only except your report file and `/tmp`. Do not commit, push or change any git state or any GitHub setting. Do not call any t3-code tools. Never run rm outside `/tmp`. No model calls, no Keychain. Network only for `127.0.0.1`, `gh api` reads and the clone in check 5. Never open `recordings/`, `DECISIONS.md`, or anything under `runs/` except `runs/demo-site/site/`. Only stop processes you started, never by name. No em dashes and no spaced en dashes. Report: PASS or NOT PASS, findings ranked (blocking, should fix, nit) with repo, file and line, the commands you ran, and what you did not check. Short.

## What came back (2026-11-03)

A fresh Claude Sonnet 5.5 (high), review 38 on `33c4754`: **PASS**, 0 blocking, 3 should fix, 5 nits. All three repos clean; the demo site works in Chromium and WebKit with all 81 clips; a fresh clone passes 249 tests; the remote holds only `main`.
- Should fix 1, the author's own user name and home path in five old commits and three review lines: left. Sasha's rule allows his own details ("besides mine, it is ok"), and removing them would need another history rewrite.
- Should fix 2, "she" and "he" for the players: left on Sasha's decision of the same day ("calling she her him his he, etc. i fine").
- Should fix 3, the video link: waits for the video.
- Fixed nits: Player 1's length reads 21:20 in the README and STATUS, as on the pages (1280.8 s); PUBLIC_CHECKLIST notes that the 2026-10-28 audit describes the old history, and step 10 sets the homepage; PRIOR_WORK names the Grok bot's fork commits. Left: the report pages' internal session ids and the old "person2" name in historical briefs.
- The reviewer ran two read-only network calls outside its allowlist in the fork (`git fetch --dry-run`, `git ls-remote origin`), no secret involved.
