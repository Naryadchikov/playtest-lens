# 40: The review before going public

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-11-03. Reviewer: a fresh Grok 4.7 xhigh through Cursor (a fresh Claude Sonnet 5.5 if Cursor's limits stop it). Read-only. Report in `docs/reviews/36-public-repo-grok.md`. Rules for reviews: docs/REVIEW.md. Only a reviewer writes PASS.

Base commit: `main` at the commit that adds this brief, in the main repo. The fork is the submodule at `game/` (branch `playtest-lens`). The demo site is a separate repo; its files are not in this checkout.

## What changed since the freeze review (task 39)

- The history of `main` was rewritten while the repo is private: `DECISIONS.md` is in no commit; the testers are named Player 1 and Player 2 instead of by who they are to the author, in every file of every commit and in commit messages; short commit hashes in the Markdown files and commit messages were mapped to the rewritten commits. Sasha's word, T3 Code chat, 2026-11-03: "yes, remove decisions from history in remote, leave local copy just for our use." and "all personal detailes should be removed from history as well, besides mine, it is ok."
- `DECISIONS.md` is git-ignored and stays only in the working folder. AGENTS.md says so; the other files mention it as plain text.
- The public docs pass: docs/THIRD_PARTY.md says "the author", STATUS.md is rewritten, docs/PUBLIC_CHECKLIST.md marks steps 7 to 9 done, docs/SUBMISSION.md holds the form's fields and drafts.

## Check

1. **The history is clean.** On every commit reachable from `main`: no `DECISIONS.md`; no word that says who a tester is to the author in any file or message; the step 4 scans of docs/PUBLIC_CHECKLIST.md (paste their output). Write your own script; do not trust ours.
2. **References still hold.** Pick at least 8 short hashes cited in docs/tasks and docs/reviews: each resolves in this repo or in the fork, and the commit it names matches what the sentence says.
3. **Nothing depends on DECISIONS.md.** A fresh clone has no `DECISIONS.md`: no Markdown link points to it, and the README, AGENTS.md and PLAN.md still read correctly without it.
4. **The new and changed docs tell the truth:** STATUS.md, docs/PUBLIC_CHECKLIST.md, docs/THIRD_PARTY.md and docs/SUBMISSION.md against README.md and the code. The SUBMISSION.md drafts make no claim the README or the code does not back.
5. **The offline tests pass:** `.venv/bin/python -m pytest -q`.

## Rules

Read-only except your report file. Do not commit. Do not call any t3-code tools. Never run rm. No model calls, no network, no Keychain. Never open `recordings/`, `runs/` or `DECISIONS.md`. Only stop processes you started, never by name. No em dashes and no spaced en dashes. Report: PASS or NOT PASS, findings ranked (blocking, should fix, nit) with file and line, the commands you ran, and what you did not check. Short.

## What came back (2026-11-03)

Grok did not start: Cursor's limits. A fresh Claude Sonnet 5.5 (high) took it, review 36: NOT PASS, 1 blocking, 3 should fix, 5 nits.
- Blocking: this brief itself quoted the relationship words. The brief's commit was amended and `main` pushed again with a lease, while private. The review report describes the words instead of repeating them.
- Fixed: docs/SUBMISSION.md's max_tokens line now matches `analyzer/client.py` (8192) and says the voice-less run was an open-weights one; STATUS.md says which checklist steps are done; PUBLIC_CHECKLIST step 11 checks that the remote holds only `main` and no tags; PLAN.md and docs/BACKUP_ORCHESTRATOR.md say DECISIONS.md is local; docs/THIRD_PARTY.md says "the main ones are listed below" and DeepSeek in the past tense.
- Left on purpose: the local tags, branches and `refs/t3/` keep the old history (Sasha: "leave local copy just for our use"); only `main` is ever pushed. Gendered pronouns for Player 1 and Player 2 are Sasha's call.

Round 2, a fresh Claude Sonnet 5.5 (high), review 37 on `a309388`: **PASS**, 0 blocking, 0 should fix, 3 nits. Fixed: the checklist's email scan reads `main` only, and STATUS.md names the commit the scans passed on. Left: the amended old commit is a loose local object, never pushed. The reviewer ran `git ls-remote origin` once (a network read the brief did not allow; no secret involved): the remote holds only `main`, equal to local.
