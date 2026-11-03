# 42: The go or no-go check before going public

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-04. Reviewer: a fresh Claude Sonnet 5.5 (high), independent of earlier reviews. Read-only. Report in `docs/reviews/39-go-public-sonnet.md`. Rules for reviews: docs/REVIEW.md. Only a reviewer writes PASS.

Sasha's ask, T3 Code chat, 2026-11-04: "ok, rerun the full test again with independed subagent on are we good to go public or not, and if yes, go public with both! and check that pages are properly working"

Your verdict decides whether two repos become public today. That is hard to take back, so report what you find, not what you expect. Do not make anything public yourself.

## What goes public

1. `Naryadchikov/playtest-lens`: this checkout, `main` at the commit that adds this brief.
2. `Naryadchikov/playtest-lens-demo`: the GitHub Pages site, checked out at `runs/demo-site/site/` (its own git repo; the only part of `runs/` you may open), `main` at `db34095`. Pages turns on after your verdict, at https://naryadchikov.github.io/playtest-lens-demo/.

Already public, and the submodule at `game/`: `Naryadchikov/cogito-playtest-lens`, branch `playtest-lens`, `9dc1183`.

Changes since the last final review (`docs/reviews/38-final-public-sonnet.md`, on `33c4754`, demo `2b5a190`, fork `1c90e48`): the demo video link in the README and on the demo front page, files removed from git or deleted, `AGENTS.md` trimmed, the fork's README and default branch, the fork's `bot/` branches deleted. Do not limit yourself to these: this is a full check.

## Check

1. **Clean, every commit that will be public** (`main` here, `main` in the demo repo, `playtest-lens` in the fork from upstream's `676be6d`): no keys or tokens, no personal emails, no tester media outside the demo repo's clips, no `DECISIONS.md`, no word that says who a tester is to the author, no tester's real name, nothing about the author's other projects or employer by name. Write your own scans. You may read `DECISIONS.md` for one purpose: to learn any tester's real name, or the name of the author's employer or other projects, so you can scan for them. Never write those names into your report or anywhere else, and do not put them on a command line that a log keeps longer than `/tmp`: describe them. The author's own name, user name and home path are allowed (Sasha, T3 Code chat, 2026-11-03: "all personal detailes should be removed from history as well, besides mine, it is ok."). "She", "he" and the like for the players are allowed by his decision of 2026-11-03.
2. **Local-only files:** `DECISIONS.md`, `STATUS.md`, `docs/VIDEO_PLAN.md`, `docs/SUBMISSION.md` and `docs/PUBLIC_CHECKLIST.md` are git-ignored and absent from `main`'s tip. All but `DECISIONS.md` remain in the history by his decision, so read them there and say if any version holds something that should stop the flip.
3. **Links:** every link in README.md, AGENTS.md, docs/THIRD_PARTY.md, docs/REVIEW.md, the demo repo's README.md and `index.html`, and the report pages' outbound links. Relative links resolve to tracked files. GitHub URLs point at the right owner, repo, branch and path. The README's GIF and the og image load from the Pages URL, so check that the file exists in the demo repo. The video link must open signed out: `curl` on `https://www.youtube.com/oembed?url=https://youtu.be/WqwKa8eM9Io&format=json` is allowed.
4. **The demo site works from a fresh clone:** clone the demo repo from GitHub into `/tmp`, serve it on `127.0.0.1` with a server you start and stop yourself, and open the front page and the three reports in Chromium and WebKit. Playwright is in this checkout's `.venv`, but its default browsers are a different version: launch with `executable_path`, `~/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell` for Chromium and `~/Library/Caches/ms-playwright/webkit-2359/pw_run.sh` for WebKit. Never run `playwright install`. If an engine will not launch, say so and go on. No console errors, no 4xx or 5xx (`net::ERR_ABORTED` on a clip the browser no longer needs is normal, but check it), no outside requests, every clip a report references exists and plays, links between pages work. Open `lobby-player-1.html#m21`: it must show Moment 21 at 19:17, and the visible clip must be `c01157.00.mp4` and play. Captures in `/tmp/t42/`.
5. **What the media shows:** pull a sample of frames from at least 10 clips across both players, plus `preview.jpg` and `report.gif`, and look at them: no desktop, notifications, file paths, real names or anything private on screen. Check the media files' metadata too.
6. **Wording:** README.md and the demo front page read as one story: the same numbers (lengths, kept and dropped counts, costs, model names), no claim the code does not back, no chat voice or internal notes a judge would trip on. Read `AGENTS.md` as a judge would: is anything there embarrassing or wrong now, and do its pointers still work? Words are Sasha's call: propose, do not rewrite. No em dashes or spaced en dashes in text agents wrote for the public.
7. **A fresh clone works:** `git clone --recursive` of this repo from GitHub into `/tmp`, then the offline tests with this checkout's `.venv` (`<checkout>/.venv/bin/python -m pytest -q`). Report the count.
8. **Ready to flip:** the remote holds only `main` and no tags, for both repos; local `main` equals it; nothing unexpected on GitHub (pull requests, issues, releases, workflows, Actions secrets, deploy keys, webhooks); commits rewritten on 2026-11-03 are not reachable on GitHub (take a sample sha from local refs that is not an ancestor of `main`, and read it through `gh api`); the fork's `playtest-lens` equals its remote; the remaining steps in `docs/PUBLIC_CHECKLIST.md` (10 to 12) are right and complete.

## Rules

Read-only except your report file and `/tmp`. Do not commit, push or change any git state or any GitHub setting. Do not call any t3-code tools. Never run rm outside `/tmp`. No model calls, no Keychain, and never read `~/.config/muse/`. Network only for `127.0.0.1`, `gh api` reads, the YouTube check in step 3 and the clones. Never open `recordings/`, or anything under `runs/` except `runs/demo-site/site/`. Only stop processes you started, never by name. No em dashes and no spaced en dashes. Your report will be public: never quote a key, a tester's name or any private text, only its file and line.

Report: first line names the reviewer, model, harness and the commits. Then PASS or NOT PASS. A blocking finding is anything that should stop the repos going public today; anything else is should fix or nit. Then each finding with its file and line, how you checked each numbered step, and what you did not check. End with a verdict in one sentence. Your final message to the orchestrator: the verdict, the counts, the blocking findings and the report's path, nothing more.

## What came back
