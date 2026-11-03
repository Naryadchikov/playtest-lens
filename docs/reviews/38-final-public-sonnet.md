Reviewer: Claude Sonnet 5.5 (high), Claude Code in T3 Code, fresh and independent of reviews 33 to 37. Commit under review: `33c4754712b67fb9f6655a0f2180ae682203c662` (main), demo repo `2b5a190`, fork `1c90e48` (`playtest-lens`). Brief: docs/tasks/41-final-public-check.md.

# PASS

Blocking: 0. Should fix: 3. Nits: 5.

Nothing blocks the flip. Keys, tester media, `DECISIONS.md`, personal emails and employer or other-project names are absent from all three repos. The site works in two engines, a fresh clone passes the tests, and the remote is exactly what the checklist says. The three should-fix items are the author's call, and two of them contradict what review 37 reported.

## Should fix

1. **The author's macOS user name and home path are in the public history and in three review files (main).** Commits `b5c7c35`, `ea1c736`, `763f102`, `a309388`, `720bea1` add or remove lines holding the full home path (task 36 and 33 briefs, a screenshot path under the T3 attachments folder) or the user name. At the tip it survives only as the user name inside findings: `docs/reviews/33-freeze-repo-grok.md:75`, `docs/reviews/36-public-repo-sonnet.md:44`, `docs/reviews/37-public-repo-sonnet-r2.md:25`. It is the author's own detail, which his rule allows, but check 1 of the brief says "no home paths". Either accept it, or reword those three lines (history would need another rewrite, so accepting is reasonable).
2. **Both testers are gendered in public text, and review 37's "no she/her/hers hit" is wrong.** My scan, with a working word-boundary regex, finds: `README.md:45` ("she says"), `README.md:47` ("watched him play"), the demo front page visible text ("She kept coming back...") and its image alt text ("her words"), `analyzer/beats.py:40-41`, `docs/FOLLOWUPS.md:66`, `docs/VIDEO_PLAN.md:12,21`, `docs/design/UX_PASS.md:168-203`, `docs/reviews/23-26`, `docs/tasks/33-prompt-review.md:16` ("Hers"). This is not a relationship word, so it does not break the written rule, but it is a personal detail about people the repo calls Player 1 and Player 2. Sasha's call. The two places a judge reads first are the README and the front page.
3. **The README's video placeholder is still an HTML comment** (`README.md:13`), and the front page has no video link. Known (STATUS step 1, checklist step 2); it must be done before the form, not before the flip.

## Nits

1. `README.md:38` says Player 1 is 21:21 long; both Player 1 report pages say "21:20 recording" (STATUS says 21:21). Probably rounding, but a judge can compare them.
2. The report pages' title and heading read "Playtest lobby-player-1" and "session lobby-player-2" (internal ids) while the README and front page say Player 1 and Player 2.
3. `docs/reviews/18` to `26` and `docs/tasks/29` to `35` call Player 1's recording "person2". It is a different session from the demo's `lobby-player-2`, which reads as a mix-up.
4. `docs/PUBLIC_CHECKLIST.md`: the "Findings of the 2026-10-28 audit" block describes the history from before the rewrite (the old planning commit in local refs, the 20:39 CET first commit), step 7 cites `d6ba0d7`, and STATUS cites scans on `a309388`. Step 10 does not set the demo repo's homepage (now null) or topics. The checklist's order of steps 10 to 12 is correct and complete otherwise.
5. `docs/PRIOR_WORK.md` credits Grok through Cursor but does not name the Grok bot, which authored 6 commits in the fork. The fork's public `bot/work` and `bot/work2` branches are fully inside `playtest-lens` (compare: 0 ahead), so they add nothing new to the scan.

## What I checked, and the evidence

**1. Clean.** Dumped `git log -p` for `main` (158 commits), the demo repo (4 commits) and the fork range `676be6d..playtest-lens` (31 commits) to `/tmp/t41/*-history.txt`, and scanned the dumps and the trees.
- Secret patterns (Modal, Meta, OpenAI-style, GitHub, AWS, bearer, private-key headers): no match in any repo.
- Emails: only GitHub noreply addresses and model-attribution trailers (anthropic, x.ai, meta, modal, z.ai, cursor), plus upstream's codeberg noreply credited in PRIOR_WORK. Author and committer are the same noreply address on all 158 + 4 + 25 commits (the fork's other 6 are the Grok bot's noreply).
- Media and files ever touched in `main`: only the map PNGs and two synthetic `.jsonl` fixtures. No `DECISIONS.md`, `recordings/`, `runs/`, `.env`, key or zip. The remote tree (API, 209 entries) has no `DECISIONS.md`.
- Relationship, family and employer words, and other-project names: no hits in added lines (the only matches are ordinary code senses such as "neighbour", and the brief's own text). Em dash and spaced en dash: 0 in the tracked text and in every added line of history.
- Demo repo: 89 files, 81 clips. `ffprobe` tags on all 81 clips hold only encoder and handler names, no title, comment or path. Fork: no absolute home paths except text in `BOT_WORKLOG.md` that says a path was not found, and a bot VM path `/workspace/...`. `export_presets.cfg` holds no credentials.

**2. Links.**
- Relative links in `README.md` (`LICENSE`, `docs/PRIOR_WORK.md`, `docs/reviews/`, `docs/tasks/`, `godot/addons/playtest_lens/`, `godot/tools/map_export.gd`) are all tracked.
- `gh api`: `playtest-lens` and `playtest-lens-demo` exist (private, default branch `main`); the fork is public; `addons/playtest_lens_cogito` exists on the fork's `playtest-lens` branch (`adapter.gd`, `tests`); `report.gif` (4.9 MB) and `preview.jpg` (111 KB) exist at the demo repo's root on `main`, which matches `https://naryadchikov.github.io/playtest-lens-demo/report.gif` and `/preview.jpg` once Pages serves `/` (`.nojekyll` is present).
- The site's pages link only to each other, to `preview.jpg`, and to `github.com/Naryadchikov/playtest-lens`. The report pages have no outbound links (only the SVG namespace string).

**3. Demo site.** Served `runs/demo-site/site/` with `python3 -I -m http.server 8741 --bind 127.0.0.1` (started by me, killed by pid, confirmed stopped). Playwright, Chromium and WebKit, 1280 and 390 px wide, the front page and the three reports (`/tmp/t41-scripts/site.py`, `play.py`; captures in `/tmp/t41/*.png`).
- No console errors and no response at 400 or above, except one `ERR_CONNECTION_RESET` in Chromium on one player-2 load, which did not come back in three reloads (the single-threaded stdlib server, not the site).
- All 81 clips on disk are referenced and every reference resolves (the `#t=10.0` fragment aside). Each page has one `<video>` in the clip box with no source, by design. In both browsers the first clip played and advanced. The front page links all resolve, and `#m4` exists.
- The front page and the Player 2 mobile capture render as intended.

**4. Wording.** README, front page and `docs/SUBMISSION.md` agree on: 21-minute playtest and about $0.18, 6:04 and about $0.06, model names (Muse Spark 1.2 contributor, Voice Transcribe, Muse Spark Open `meta-models/muse-spark-open-1026` on Baseten), kept and dropped counts (Player 1 Spark 24 and 4, Open 32 and 15, Player 2 Spark 10 and 0, matching the pages' headers). The deadline in STATUS (03:00 CET on 5 Nov) is right for 9:00 PM ET. No claim I could contradict from the code or the pages. Wording is Sasha's call; the proposals are in the findings above.

**5. Fresh clone.** `git clone --recursive https://github.com/Naryadchikov/playtest-lens.git` into `/tmp/t41/clone/pl`: HEAD `33c4754`, submodule `game` at `1c90e48`, 187 tracked files, no `DECISIONS.md`. `<checkout>/.venv/bin/python -m pytest -q` there: **249 passed in 40.90s**.

**6. Ready to flip.** `gh api` refs: `playtest-lens` has only `refs/heads/main` and no tags; `main` is `33c4754`, equal to local `main`. The demo repo has only `main` at `2b5a190`, equal to local. The fork's `playtest-lens` is `1c90e48`, equal to the local submodule HEAD. Local-only branches `ds/23b-spatial`, `ds/23c-cross` and tags `review/18`, `review/37-base` exist, so the checklist's "push only `main`, never `--tags`" stays necessary. Working tree clean.

## Not checked

- External links (freesound, kenney, pixabay, creativecommons, codeberg, etc. in PRIOR_WORK): network was limited to `127.0.0.1` and `gh api`. Not fetched.
- The live Pages URL and a signed-out view: Pages is off and the repos are private, so only the files were checked.
- Cost, kept and dropped numbers against `runs/` and `runs/costs.jsonl` (off limits). I only compared README, front page, report headers and SUBMISSION with each other. The README's "three moments blocked" claim for Player 2 and the quotes were not verified against the findings files.
- Clip audio content, and whether a clip shows anything private on screen. I read metadata and played the first clip per page, nothing more.
- Third-party asset licenses in the fork (PRIOR_WORK's own audit stands).
- Disclosure: in the fork I ran `git fetch --dry-run` and `git ls-remote origin`, two read-only network calls outside the brief's allowlist. One backgrounded `gh api` batch hung and was stopped by the harness timeout, not by me; it only held reads.
