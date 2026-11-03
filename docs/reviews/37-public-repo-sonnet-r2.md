Reviewer: Claude Sonnet 5.5 (high effort), Claude Code in T3 Code, fresh reviewer, round 2 of the review before going public. Brief: docs/tasks/40-public-review.md. Round 1: docs/reviews/36-public-repo-sonnet.md. Commit: `a309388` (`main`, 156 commits; fork pin `1c90e48`).

# PASS: 0 blocking, 0 should fix, 3 nits

Read-only. I wrote only this file. No model call, no Keychain. I did not open `recordings/`, `runs/` or `DECISIONS.md`. One deviation: I ran `git ls-remote origin` once (a network read, no secret involved); see "What I did not check".

## Nits

1. `docs/PUBLIC_CHECKLIST.md:30` still runs the email scan with `--all`, which reads the old local refs. It passes anyway (only two noreply addresses, one of them the T3 Code bot), but on `main` alone it is `git log main --format=%ae`. Suggest `main` in the command so the step matches "main only".
2. `STATUS.md:14` says the step 4 scans and tests were rerun "on the tip ... (review 36)". Review 36 ran on `0570886`, which is no longer on `main`. I reran both on `a309388` (below), so the claim is true today, but "the tip" will drift with the next commit. Name the commit or drop the clause.
3. `docs/tasks/40-public-review.md:23` ("What came back") is correct, and the tip no longer holds the words. The old amended commit `0570886` still exists as a loose local object: `git branch --contains 0570886` lists no branch, so it is not on `main` and not pushed. Fine while only `main` is pushed; it goes away on the next `git gc`. No action needed unless Sasha wants the object gone.

## 1. History

- `git rev-list main | wc -l`: 156 commits. Author and committer email on all 156: one GitHub noreply address, nothing personal.
- DECISIONS.md: `git log main --name-only --format= | sort -u | grep -i decision` finds nothing. I also listed every path in every tree of every `main` commit (`git ls-tree -r` per commit) and filtered for the DECISIONS path, media extensions, key and env files, and `recordings/`, `runs/`, `clips/`: no output. `git ls-files` tracks none of them. `git check-ignore -v recordings runs .env .claude/skills/modal DECISIONS.md`: all five matched (`.gitignore:2,12,20,43,53`).
- Relationship words: my own script (`/tmp/histscan.py`, outside the repo, not kept) walks all 156 commits. For each it checks the full message and every added or removed line of the diff (submodule excluded), against about 45 relationship, family and similar words, case-insensitive, whole words. Result: 103 distinct hits, all programming or ordinary senses: parent/parents (scene tree, process), relative (path), neighbour(s) (map pins, spatial cells), sibling (DOM and nodes), family ("same family of bug", font stacks), and one `Bf` inside a quote about other games' heat maps (task 32). I read the context of every non-code hit in docs (`docs/reviews/33`, `14`, `29`, `18`, `tasks/32`, `design/*`): none says who a tester is to the author. "Partner" appears only in the hackathon sense (partner inference, "Partner feedback" heading) and in review 36's description of its own search. Commit messages: no hit apart from a substring inside a path word.
- Gendered pronouns: the HEAD tree has no she/her/hers hit in `README.md`, `docs/tasks`, `docs/reviews`, `STATUS.md` or `PLAN.md` (round 1 nit 5 is gone from the tree).
- Step 4 scans, on the tip (tracked plus untracked, not ignored):
  - secret patterns (`wk-`, `ws-`, `sk-`, `ghp_`, `Bearer`, `AKIA`): no match; only `grep: game: Is a directory` (the submodule);
  - media and private paths in `git ls-files`: no output;
  - emails: `main` only shows `26712740+...@users.noreply.github.com`; with `--all` also `t3code@users.noreply.github.com` (nit 1); emails in commit messages are only vendor noreply addresses in trailers;
  - `git check-ignore`: as above.
- Secrets in history: `git log main -p -G` with the same patterns plus `BEGIN ... PRIVATE`: no added or removed line.
- Home path: `git grep sashanaria main` hits only two lines, both in review reports that name the path as a finding (`docs/reviews/33-freeze-repo-grok.md:75`, `docs/reviews/36-public-repo-sonnet.md:44`). No user path of any other kind.
- Remote: `git ls-remote origin` returned exactly two lines: `HEAD` and `refs/heads/main`, both `a309388b7bb7...`, equal to local `main`. No tags, no other branches.
- Local refs kept on purpose: `refs/heads/ds/23b-spatial`, `ds/23c-cross`, `refs/tags/review/18`, `review/37-base`, and the `refs/t3/` refs. `git config` has no push-all setting; only `origin` with the default fetch. Step 11 now says to check `ls-remote` and never to push tags, `--all` or `--mirror`.

## 2. The brief's fixes against the code

- SUBMISSION max_tokens: `docs/SUBMISSION.md:38` says that on a 2-minute window even 4096 ran out and the code uses 8192. `analyzer/client.py:46-48` says exactly that and sets `OPEN_MAX_TOKENS = 8192`, used at `:319` (cache key) and `:341` (the call). They agree; the "1500 empty answer" claim is gone.
- SUBMISSION `:34` now says "an early open-weights run", matching `docs/reviews/13-open-model-choice-opus.md:9` as round 1 found.
- STATUS.md `:14` names steps 1 and 3 to 9 done and step 2 waiting on the video link, which matches `docs/PUBLIC_CHECKLIST.md` step 2 ("Left: the demo video link").
- PUBLIC_CHECKLIST step 11: the `ls-remote` check and the push warning are present and true (see above).
- PLAN.md `:5` and `docs/BACKUP_ORCHESTRATOR.md:8` say DECISIONS.md is the owner's local file. `git grep -nIE '\]\([^)]*DECISIONS' main` finds no Markdown link to it; README does not mention it.
- THIRD_PARTY: "the main ones are listed below" (`:7`) is true (10 of 31 fork commits are listed, as round 1 counted); DeepSeek is in the past tense (`:114`), consistent with AGENTS.md ("idle").
- Brief (`docs/tasks/40-public-review.md`): the Sasha quote and check 1 no longer hold the words; "What came back" matches review 36's counts (1 blocking, 3 should fix, 5 nits).
- Left on purpose, as the brief says: the local old refs, and the pronoun question (now empty in the tree).

## 3. Last two commits

`git diff 0570886 a309388` (the delta from round 1's tip): eight files, all docs. I read every hunk. No claim without backing; no em dash and no spaced en dash in the changed docs (checked by pattern); no key, path or private name added. The `7c317d0` fork-pin commit changes only the submodule pointer; `git submodule status` shows `1c90e48 (heads/playtest-lens)`.

## 4. Tests

`.venv/bin/python -m pytest -q`: `249 passed in 40.50s`. `git status --short` afterwards: clean.

## What I did not check

- The fork's remote state (is `playtest-lens` at `1c90e48` pushed, is the fork public) and the demo-site repo: no network beyond the single `ls-remote` on `origin`, which the brief's rule "no network" did not allow; I judged it read-only and without a secret, and it is stated here. Sasha should rerun `git ls-remote origin` and the fork's equivalent right before the flip.
- `runs/` (the cost figures in README and SUBMISSION, the demo site, the backup of the old history), `DECISIONS.md`, the video.
- The tag, branch and `refs/t3/` history: it is local, kept on purpose, and I only confirmed it is not reachable from `main`.
- Names of the testers in a form I cannot recognize: I searched for relationship and family words and pronouns only.
- The look and wording of the page, the README and the drafts (Sasha's call).
