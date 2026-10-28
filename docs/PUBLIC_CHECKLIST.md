# Going public: the last step

The repo is private for now (Sasha, 2026-10-27, DECISIONS.md: "I'll make it public before we submit"). Make it public as the last step, after the freeze review, by running this list on the exact commit that will be public. Sasha flips the visibility; agents run the checks. First audit by the Claude Sonnet 5.5 orchestrator on 2026-10-28.

## Findings of the 2026-10-28 audit

- **Secrets:** a scan of every tracked and untracked file for Modal (`wk-`, `ws-`), Meta, GitHub, OpenAI-style and AWS key patterns found nothing. Keys live only in the Keychain.
- **Media:** no recording, clip, audio or video is tracked in this repo. `recordings/`, `clips/`, `runs/` and the media extensions are ignored. Godot's session logs are written to `user://`, outside the repo. The one tracked `.jsonl` is a synthetic test fixture.
- **History:** every commit's email is a GitHub noreply address, none is a personal address. The first commit is 2026-10-26 20:39 CET, after the kickoff. The early planning zip was removed from `main` and from the remote (`origin` has only `main`); the old commit survives only in local `refs/t3/...` checkpoint refs, which are never pushed.
- **The fork** (`cogito-playtest-lens`): already public, upstream history from before the kickoff is expected and credited in docs/PRIOR_WORK.md. Its tracked third-party audio and fonts have licenses recorded there.
- **Private names:** no mention of Sasha's other games or his employer in tracked files. No absolute home paths.

## Do before the visibility flip

1. **LICENSE:** the copyright line still reads `__AUTHOR__`. Sasha gives the name to use.
2. **README:** replace the "How to run it comes here once it runs" line and the stale agent list with the real run steps, the three modes, the open-weights result, the demo video link, and the score table. Problem first, then the solution.
3. **Hackathon rules:** the official rules text is not in the repo. A secondary listing (Internshala, unverified) gives the deadline as 2026-11-05 06:30 IST, which is 2026-11-04 20:00 ET, an hour earlier than the 21:00 ET in AGENTS.md. Sasha checks the official page and the exact deadline, then the orchestrator writes the verified rules and the deliverables checklist (video length, repo, README, license, open-weights prize terms) into this file.
4. **Rerun the scans on the final commit,** in the main repo and in the fork:
   - `git ls-files -co --exclude-standard | xargs grep -InE 'wk-[A-Za-z0-9]{10,}|ws-[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|Bearer [A-Za-z0-9._-]{20,}|AKIA[0-9A-Z]{16}'` shows nothing;
   - `git ls-files | grep -Ei '\.(mp4|mov|mkv|webm|wav|m4a|zip|key|pem|env)$|recordings/|runs/'` shows nothing outside the fork's licensed game audio;
   - `git log --all --format=%ae | sort -u` lists only noreply addresses;
   - `git check-ignore -v recordings runs .env .claude/skills/modal` matches every path.
5. **Tester privacy:** no tester video, audio, name or message anywhere in the repo or the docs. Sasha's own recordings stay out too. The demo's clips are shown in the video only, or added only with Sasha's yes.
6. **PRIOR_WORK.md:** complete. COGITO and its assets, Montserrat and OFL, every CC0 sound, the dev tools (DeepSeek on Modal, Grok, Claude), and any new add-on or library added since.
7. **The fork's `playtest-lens` branch** holds every logger change that main relies on, pushed, and a fresh `git clone --recursive` of the public repo builds and runs the offline tests.
8. **Docs that go public:** DECISIONS.md, docs/tasks, docs/reviews and STATUS.md quote Sasha's chat. Sasha reads DECISIONS.md once and says yes or names lines to cut. Remove or tidy STATUS.md's day-to-day notes.
9. **Visibility:** Sasha makes `playtest-lens` public in GitHub settings, sets the repo description and topics, and checks that the fork is public too. Open the public URL in a signed-out browser.
10. **Submit** only after step 9, with the public URL.
