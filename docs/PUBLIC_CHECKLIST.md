# Going public: the last step

The repo is private for now (Sasha, 2026-10-27, DECISIONS.md: "I'll make it public before we submit"). Make it public as the last step, after the freeze review, by running this list on the exact commit that will be public. Sasha flips the visibility; agents run the checks. First audit by the Claude Sonnet 5.5 orchestrator on 2026-10-28.

## Findings of the 2026-10-28 audit

- **Secrets:** a scan of every tracked and untracked file for Modal (`wk-`, `ws-`), Meta, GitHub, OpenAI-style and AWS key patterns found nothing. Keys live only in the Keychain.
- **Media:** no recording, clip, audio or video is tracked in this repo. `recordings/`, `clips/`, `runs/` and the media extensions are ignored. Godot's session logs are written to `user://`, outside the repo. The one tracked `.jsonl` is a synthetic test fixture.
- **History:** every commit's email is a GitHub noreply address, none is a personal address. The first commit is 2026-10-26 20:39 CET, after the kickoff. The early planning zip was removed from `main` and from the remote (`origin` has only `main`); the old commit survives only in local `refs/t3/...` checkpoint refs, which are never pushed.
- **The fork** (`cogito-playtest-lens`): already public, upstream history from before the kickoff is expected and credited in docs/PRIOR_WORK.md. Its tracked third-party audio and fonts have licenses recorded there.
- **Private names:** no mention of Sasha's other games or his employer in tracked files. No absolute home paths.

## Do before the visibility flip

1. **LICENSE:** done (Aleksandr Nariadchikov).
2. **README:** rewritten on 2026-11-01 (problem first, three playtests, the held-out check, Meta's models, open-weights mode, run it, the add-on, how it was built). Left: the demo video link in the comment under the GIF.
3. **Hackathon rules** (verified from the Participant Guide Sasha sent on 2026-10-28; the Internshala deadline I found earlier was wrong):
   - Submission due **Wed 2026-11-04, 9:00 PM Eastern (EST)** on the Cerebral Valley platform. Late submissions are not considered. Building period 2026-10-27 to 2026-11-04; kickoff was Mon 2026-10-26, 12:00 ET. Our first commit is 2026-10-26 20:39 CET, a planning commit made after the kickoff and before the building period: answered: Sasha, T3 Code chat, 2026-10-31: "It was said both on discord and FQA that dev starts once first stream is finished or something along those lines, so we made all good".
   - The repository must be public; the video link must be reachable; everyone who worked on it is listed on the submission page (solo here).
   - A three-minute demo video that highlights only what was built during the hackathon. Judges must be able to identify the new work. COGITO, Godot and the assets are prior work: say so in the video and in PRIOR_WORK.md.
   - New work only; no code, data or assets without the rights to them.
   - The project must use Meta's models. Rubric (0 to 10): Impact 30%, Use of Meta AI Tooling 25% (beyond a basic integration), Technical Depth and Execution 20%, Demo 25%. Stage one is pass or fail on theme fit and real use of Meta's models.
   - Anti-projects named in the guide include sports analyzers or coaches and simple image analyzers: the README and the video should make clear this is a multi-source analyst (video, voice, event log) for game developers.
   - Bonus prizes in reach: Best Build on Meta Open Weight Models ($10,000: Muse Glimmer or Muse Spark Open, own hardware or partner inference, so Modal or Baseten counts), Best Agentic Use-Case ($5,000), Most Viral Project ($20,000, a demo post on X) and Community Vote ($10,000, public gallery).
   - Baseten: use `meta-models/muse-spark-open-1026`, not `muse-spark-open` (the guide says so).
   - Credits: Meta's $150 must be claimed by the same deadline, and the Modal $100 is offered for running Meta's open-weight models through Endpoints. Sasha's agent work on DeepSeek, GLM and Kimi has drawn on his Modal credits so far (billing summary, 2026-10-28): keep that small if those credits are meant for Meta models.
4. **Rerun the scans on the final commit,** in the main repo and in the fork:
   - `git ls-files -co --exclude-standard | xargs grep -InE 'wk-[A-Za-z0-9]{10,}|ws-[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|Bearer [A-Za-z0-9._-]{20,}|AKIA[0-9A-Z]{16}'` shows nothing;
   - `git ls-files | grep -Ei '\.(mp4|mov|mkv|webm|wav|m4a|zip|key|pem|env)$|recordings/|runs/'` shows nothing outside the fork's licensed game audio;
   - `git log --all --format=%ae | sort -u` lists only noreply addresses;
   - `git check-ignore -v recordings runs .env .claude/skills/modal` matches every path.
5. **Tester privacy:** no tester video, audio, name or message anywhere in the repo or the docs. Sasha's own recordings stay out too. The demo's clips live only in the separate demo repo, with all three players' yes (Sasha, 2026-11-01: "all 3 players are ok with sharing their data"); this repo holds none, and the README's GIF loads from the demo site.
6. **PRIOR_WORK.md:** complete. COGITO and its assets, Montserrat and OFL, every CC0 sound, the dev tools (DeepSeek on Modal, Grok, Claude), and any new add-on or library added since.
7. **The fork's `playtest-lens` branch** holds every logger change that main relies on, pushed, and a fresh `git clone --recursive` of the public repo builds and runs the offline tests.
8. **Docs that go public:** docs/tasks, docs/reviews, AGENTS.md, docs/PRIOR_WORK.md and STATUS.md quote Sasha's chat in places (AGENTS.md, PRIOR_WORK.md and the task 18 brief carry his verbatim quotes). Sasha reads them once and says yes or names lines to cut. Tidy STATUS.md's day-to-day notes.
9. **Remove DECISIONS.md from the public history** (Sasha, 2026-10-28, wants it gone from the public release and its commits cleaned): do it while the repo is still private, then flip. See "DECISIONS.md removal" below.
10. **The demo site** (`Naryadchikov/playtest-lens-demo`, private, pushed 2026-11-01 from `runs/demo-site/site/`, its own git repo; Pages off). GitHub Pro can build Pages from a private repo, but the published site is public anyway (access control for Pages is Enterprise Cloud only), so Pages is switched on only at the green light:
    - `gh repo edit Naryadchikov/playtest-lens-demo --visibility public --accept-visibility-change-consequences`
    - `gh api -X POST repos/Naryadchikov/playtest-lens-demo/pages -f 'source[branch]=main' -f 'source[path]=/'`
    - open https://naryadchikov.github.io/playtest-lens-demo/ signed out: the front page, the three reports, a clip playing, and the README's GIF (it loads from the site).
11. **Visibility:** Sasha makes `playtest-lens` public in GitHub settings, sets the repo description and topics, and checks that the fork is public too. Open the public URL in a signed-out browser.
12. **Submit** only after steps 10 and 11, with the public URL and the video link.

## DECISIONS.md removal

Possible, with these limits. The file touches 10 commits, and 9 other files link to it. A plain `git rm` only hides it from the latest tree: the old commits keep it, and anyone can read it from the history.

1. **While still private, rewrite the history** so no commit contains `DECISIONS.md`: `git filter-branch --index-filter 'git rm --cached --ignore-unmatch DECISIONS.md' -- --all` (Git 2.54 is installed; `git filter-repo` is not, and would need Sasha's yes to install). Back up first: a private copy of the file and of the repo outside the repo folder.
2. **Force-push `main`** to the private remote. AGENTS.md and Sasha's global rules forbid force-pushing the default branch, so this needs his explicit word for that push at that time. The T3 checkpoint refs under `refs/t3/` stay local and are never pushed.
3. **Only then flip to public.** If the repo is made public first, GitHub can keep the old commits reachable by SHA and in forks, and a rewrite no longer helps.
4. **Clean the links and quotes:** replace the references in the 9 files with the short rule they point to, drop `DECISIONS.md` from `.gitignore`-tracked reading lists, and review the verbatim quotes in AGENTS.md, docs/PRIOR_WORK.md and docs/tasks/18-telemetry-volumes.md. Commit messages that name decisions (1 does) are rewritten by the same pass only if Sasha wants them cut.
5. **Keep the file for agents.** After the flip the working copy stays in the folder, git-ignored, and a private copy lives in Sasha's agent-rules repo or another private place, because AGENTS.md calls it the source of truth. Fresh clones will not have it: the public README must not depend on it.
6. **Cost of removing it:** judges lose the readable trail of who decided what. Commit trailers still name each author model, and PRIOR_WORK.md says what is prior work. This is Sasha's call; the orchestrator recommends keeping a short public DECISIONS-free "How this was built" section in the README instead.
