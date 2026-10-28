# Reviews

Proposed by Claude Opus 5.5 in Sasha's claude.ai chat, 2026-10-26; Sasha confirmed it the same day (DECISIONS.md). It's a lighter version of a loop he already runs: there are no PRs here, and nine days.

## When

- **Every task:** the orchestrator reads the whole diff and runs the checks before it commits (AGENTS.md, "Working with the authors").
- **A milestone,** not every commit: the end of a piece in PLAN.md's days (the Spark test, the add-on, the checking pass, the report page, the summary). A fresh Grok 4.7 xhigh reviewer reviews it (DeepSeek for Grok-authored work). For the checking pass and the score, the review also checks that no tuning read the held-out notes. The orchestrator tags the reviewed commit `review/NN` so the next round can diff from it.
- **One UX review of the report page's captures and the README,** by Claude when its limits return (Saturday evening, 2026-10-31), or earlier if Sasha picks another model.
- **The freeze** (PLAN.md, Tue Nov 3): one fresh reviewer on the whole repo, Claude Opus 5.5 if its limits are back. Not the orchestrator's thread: after nine days it's anchored on its own briefs.

## The loop

1. **A new reviewer each round,** as a subagent, on a different model than the author (AGENTS.md, "Who does what"). A reviewer resumed from an earlier round tends to recheck its own old findings. Claude's usage is the scarce one: brief any Claude review on the diff and the evidence, not the whole history.
2. **The brief stands alone:** the commit, the last reviewed tag, what the milestone must do with Sasha's decisions quoted, and the earlier rounds' findings, so the reviewer checks they stay fixed. It says "Do not call any t3-code tools" and "never run rm" (AGENTS.md, "How to work", says why and when that line can go).
3. **The report** goes to `docs/reviews/NN-<milestone>-<reviewer>.md`. Its first line names the reviewer, model and harness, and the commit. Then PASS, or NOT PASS with the count of blocking findings. Then the blocking findings, then the nits, each with a file and a concrete failure. Only a reviewer's report says PASS.
4. **The fix.** Check each finding against the code, fix the real ones, and say in the report file why the rest are dismissed. A new commit needs a new pass.
5. **Name the class, fix every instance.** A finding names its class of bug; before the fix commit, grep for the whole class.
6. **Pre-existing findings don't block.** They go to [FOLLOWUPS.md](FOLLOWUPS.md).
7. **From round 2,** a review reads the diff since the last reviewed commit plus the earlier findings.
8. **The round cap.** If round 2 is still NOT PASS, stop and bring Sasha the approach question instead of a round 3.
9. **What the checks don't cover.** Every milestone report to Sasha ends with this section, so he knows where to look.

## What a reviewer checks

- **Code and tech only:** correctness, tests, cost and key safety, the public-repo rule. Never the product's wording, the look, or Sasha's decisions.
- **The quality bar** in AGENTS.md, "When to switch to more Claude": the reviewer checks the orchestrator's evidence for each line, and reruns one line itself.
- **The analyzer:** the tests pass with cached replies and no API calls; every model call goes through the client (cache and cost line); the report page computes nothing; no tuning touched the held-out notes.
- **The Godot side:** the add-on's headless check passes; the add-on changes no gameplay; the fork's branch holds only the listed changes.
- **Every diff:** no key, token, recording or private file; no em dashes or spaced en dashes in what agents wrote.

## Misses

One line for each thing Sasha found that had passed review: the area, what it was, which check should have caught it, and the check added. Misses decide when an area moves to Claude (AGENTS.md, "When to switch to more Claude").
