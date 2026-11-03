Orchestrator's note (Claude Opus 5.5, 2026-11-03): the relationship words this report searched for are replaced by a description, so the report does not repeat what it found.

Reviewer: Claude Sonnet 5.5 (high effort), Claude Code in T3 Code, fresh reviewer (Cursor's limits stopped the Grok reviewer before it started). Task: docs/tasks/40-public-review.md. Commit: `0570886` (`main`, 155 commits; fork pin `1c90e48`).

# NOT PASS: 1 blocking, 3 should fix, 5 nits

Read-only. I wrote only this file. No model call, no network, no Keychain; I did not open `recordings/`, `runs/` or `DECISIONS.md` (only checked that git tracks none).

## Blocking

1. **The tip commit holds the relationship words.** `docs/tasks/40-public-review.md:9` quotes Sasha's rule with the two relationship words in it, and `:15` lists them as search terms. The words are in the brief, not in a description of a tester, but the quote tells a reader which relationships the two testers have, which is what the rule removes. Check 1 ("no relationship words in any file or message") fails on `0570886`.
   - Evidence: `git log main -i -S<word>` for four relationship words returns only `0570886` for each (4 hits across the 4 words, all in this one file). Every other commit is clean.
   - Fix: rephrase the brief without the words (for example "no wording about who the testers are to the author"; Sasha's full quote can stay in his local DECISIONS.md), amend the tip while the repo is still private, and push `main` again with `--force-with-lease`. A change to the tip needs a new pass.
   - Class: Sasha's own quotes that name the thing they ask to remove. Grep result for the whole class is above; nothing else in the tree.

## Should fix

2. **Old history is still in local refs that one wrong push would publish.** `git for-each-ref` shows `refs/tags/review/18`, `refs/tags/review/37-base` and `refs/heads/ds/23b-spatial`, `refs/heads/ds/23c-cross` pointing at the pre-rewrite history (none is an ancestor of `main`), plus about 100 `refs/t3/...` checkpoint refs (761 commits under `--all`, 155 under `main`). `git log refs/tags/review/37-base` still touches `DECISIONS.md` in 33 commits and has 4 commits with a relationship word. `origin` has only `main` and the config has no push-all setting, so nothing is public now, but `git push --tags`, `--all` or `--mirror` would publish it. The step 4 email scan uses `--all`, so it also reads the old refs. Fix: delete or retarget the four tags and branches (the owner's call; I do not touch git state), and add to PUBLIC_CHECKLIST step 11 a check that `git ls-remote origin` lists only `main` and no tags.
3. **`docs/SUBMISSION.md:38` contradicts the code.** The Baseten feedback says "at 1500 we got an empty answer, and 4096 works". `analyzer/client.py:46-48` says "4096 was used up before the answer on a 2-minute window" and sets `OPEN_MAX_TOKENS = 8192`. A judge reading the code will see the draft is wrong. Fix: say the code uses 8192 and why.
4. **`STATUS.md:14` over-claims.** "docs/PUBLIC_CHECKLIST.md steps 1 to 9 are done." Step 2 itself says "Left: the demo video link". Step 4 says to rerun the scans on the final commit and no tracked file records that run (mine is below, on `0570886`). Step 7's 249 passed was on `d6ba0d7`; I get 249 on the tip, so the number holds, but the line should name the commit it was checked on. Fix: say which steps are done and which are left.

## Nits

5. `README.md:45,47` and some commit messages and task briefs say "she", "her", "him", "Hers" about Player 1 and Player 2 (for example `docs/tasks/33-prompt-review.md:16`, `docs/tasks/37-report-build-mix.md:48`; commit messages with "Her 14:02 Code Lock moment"). Not a relationship word, so it does not fail check 1, but Sasha said all personal details go. His call whether gender counts; a neutral wording ("the player") costs a few lines in README and the briefs.
6. `PLAN.md` cites DECISIONS.md nine times (for example `PLAN.md:26,27,33,43,47,58`) and `docs/BACKUP_ORCHESTRATOR.md:8` says to read it, with no note that a fresh clone has no such file. Only AGENTS.md:5 says so. README does not mention it, so it reads fine. One line near the top of PLAN.md ("DECISIONS.md is the owner's local log and is not in this repo") closes it.
7. `docs/THIRD_PARTY.md:7` says "Our changes are only the commits on its `playtest-lens` branch, listed below", and `:96-110` lists 10 commits. The branch has 31 commits above `676be6d` (`git -C game log 676be6d..HEAD`): `03ba23f`, `6e4e0ad`, `dc8c771`, `aee94ef`, `c10c2d0`, `95b8704`, `eab665d`, `b0a52cf`, `588c6a3`, `290cba9`, `8049b5d` and more are not listed. All are new work, so no rule is at risk, but "listed below" is not true.
8. `docs/THIRD_PARTY.md:114` says DeepSeek "writes part of the code" in the present tense; AGENTS.md says DeepSeek, GLM and Kimi are idle.
9. `docs/SUBMISSION.md:34`, "When an early run saw the video without the voice, it did worst against the developer's notes": the only support in the tree is `docs/reviews/13-open-model-choice-opus.md:9`, a Muse Spark Open run on Modal, judged by a reviewer who did not watch the footage. Say "an early open-weights run". The cost figures (about $0.18, $0.06, $0.09, $2.30 and so on, `README.md:7,40,41`) come from the git-ignored `runs/costs.jsonl`; I could not check them.

## 1. History (commands and results)

All commands from the repo root, read-only.

- `git rev-list main | wc -l`: 155 commits. `git log main --format='%an <%ae> | %cn <%ce>' | sort | uniq -c`: 155 of `Aleksandr Nariadchikov <26712740+Naryadchikov@users.noreply.github.com>`, author and committer.
- `git log main --name-only --format= | sort -u | grep -i decision`: no output. `git ls-files | grep -i decisions`: none. `git check-ignore -v DECISIONS.md recordings runs .env .claude/skills/modal`: all five matched (`.gitignore:53,2,12,20,43`).
- Relationship words, content: `git log main -i -S<word>` for 16 relationship and family words: only four hit, only on `0570886` (blocking 1). `partner` hits three commits (`cdc12dc`, `31e07d7`, `ecce194`), all "partner feedback" and "partner inference" about the hackathon, not a person.
- Relationship words, messages and trailers: `git log main --format=%B | grep -inE` on the same list with word boundaries: only `he places the boxes and records with OBS` (the author himself) and the pronoun lines in nit 5.
- Step 4 scans, on the tip (tracked plus untracked-not-ignored):
  - Secret patterns (`wk-`, `ws-`, `sk-`, `ghp_`, `Bearer`, `AKIA`): no match (exit 1). The only output was `grep: game: Is a directory`, the submodule.
  - Media and private paths: `git ls-files | grep -Ei '\.(mp4|mov|mkv|webm|wav|m4a|zip|key|pem|env)$|recordings/|runs/'`: no output.
  - `git log --all --format=%ae | sort -u`: `26712740+Naryadchikov@users.noreply.github.com`, `t3code@users.noreply.github.com`.
  - `git check-ignore`: as above.
- My own scans over all of `main`'s history: secret patterns plus `api_key = "..."` and `-----BEGIN` in every diff (`git log main -p -G...`): no hit. Every path ever in `main` with a media, key or private extension or in `recordings/`, `runs/`, `clips/`: only `tests/fixtures/session_log.jsonl` and `tests/fixtures/spatial_log.jsonl`, the synthetic fixtures. Emails in messages and trailers: only `noreply` addresses of the model vendors. Emails in the tree: only noreply addresses and the upstream author's Codeberg noreply handle, inside review 33.
- Home paths: `git grep -n sashanaria HEAD` hits only `docs/reviews/33-freeze-repo-grok.md:75`, a finding that names the files it was in. No tracked task brief still holds a `/Users/` path.
- First commit: `2026-10-26 20:39:37 +0100`, after the 12:00 ET kickoff (17:00 CET). Matches PUBLIC_CHECKLIST.

## 2. References

43 backticked short hashes in `docs/tasks` and `docs/reviews`, plus 17 full-length hashes: every one resolves in `main` or in the fork (`git cat-file -t`, `git -C game cat-file -t`), apart from file checksums that look like hashes (`8305c4c...`, `85ca0cc...`, `e6c7dd3...`, `4dcbc7c...`, `5f6fe87...`, which sit next to the words shasum or sha256). Spot checks of what the sentence says against the commit subject (all match):

| Hash | Where | Commit |
|---|---|---|
| `3c5c920` | reviews/12:3 | main, "Add a time trail and a separate heat map on the report" (as quoted) |
| `952ecb1` | tasks/37:73 | main, "Report: fix reviews 23 and 24 (task 38)..." |
| `ded2110` | reviews/25:7 | main, "Reviews 23 (Grok, code) and 24 (Sonnet, UX 7.4): both NOT PASS; task 38..." |
| `b24db37` | tasks/37:74 | main, "Report: review 28 (UX 8.4): the phone stacks in normal flow..." |
| `5d7400a`, `f397f7e` | tasks/37:75 | main, the half-screen layout and the revert |
| `75777b5`, `f63a455` | reviews/17:12 | main, the prompt rewrite and "Fold one struggle in a room into one card" |
| `2203ed7`, `9646a66` + fork `a9f78ac` | reviews/21:5 | main "Point at fork a9f78ac", main "Move the Godot add-on into this repo", fork "The add-on's source moves to the main repo" |
| `5acc6a4` + fork `0390930` | reviews/19:32 | main "Map JSONs record their hidden nodes; review 19 round 1", fork "map_export: reject bad numbers and boxes; record hidden nodes" |
| `e8511f3`, `974a1b2` | reviews/33:1 | main "Polish: README for the three playtests...", "Task 39: the freeze review brief" |
| `763f102`, `7e32700` | tasks/39:34,35 | main "Review 33 fixes...", "Review 34 fixes..." |
| fork `b0b3647`, `8049b5d`, `b0a52cf`, `dc8c771`, `1bd0281` | tasks/25, 24, 22, 31 | fork subjects match each task's sentence |

The 10 fork commits listed in THIRD_PARTY.md:98-110 all exist in the fork, in the same order and with the quoted subjects. `c10fbc2` (reviews/18:24, "a render from c10fbc2") is the commit just before the polish commit `b36e564` and is consistent with "before".

## 3. DECISIONS.md

- No Markdown link points to it: `git grep -nIE '\]\([^)]*DECISIONS' HEAD` finds nothing. It appears as plain text in 29 files; `.gitignore:52-53` ignores it and AGENTS.md:5 says a fresh clone does not have it.
- README.md has no mention. AGENTS.md reads correctly (the rules say where it lives). PLAN.md reads, but see nit 6.

## 4. The docs against README and code

Checked and true: STATUS.md's roles match AGENTS.md; the deadline arithmetic (9:00 PM EST Wed 4 Nov is 03:00 CET Thu 5 Nov; 18:00 CET Wed is 12:00 EST); README's flow against code (120 s windows with 20 s overlap `analyzer/analyze.py:28`, `spark_test.py:63`; 20 s clips `check.py:32`; quote kept only if in the transcript `check.py:190-195`; separate `input_audio` wav for the open model `client.py:312-334`; default model ids `client.py:36-48`, `analyze.py:27`); SUBMISSION's Meta-product list matches README "Use of Meta's models"; THIRD_PARTY's third-party list is complete for what the README names; PUBLIC_CHECKLIST step 9 matches the state (no DECISIONS.md in any `main` commit). Not true or loose: findings 3, 4, 7, 8, 9.

## 5. Tests

`.venv/bin/python -m pytest -q`: `249 passed in 40.50s`, exit 0. `git status --short` after: clean.

## What I did not check

- The remote and the fork's push state: no network. The fork's `origin/playtest-lens` tracking ref in `game/` is stale (at `676be6d`, no upstream configured), so I could not confirm that `playtest-lens` at `1c90e48` is pushed, or that `origin/main` on GitHub equals local `main`. Run `git ls-remote` for both before the flip.
- `runs/` (the cost figures, the demo site, the backup of the old history), the demo-site repo, the video, `DECISIONS.md`.
- The Godot add-on and report page code beyond what the docs cite; the look and wording of any page (Sasha's call).
- Whether names of the testers appear in forms I cannot recognize (I do not know them): I searched for relationship words and gendered pronouns only.
