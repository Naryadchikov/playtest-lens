---
name: validate-change
description: Check a finished change to Playtest Lens before calling it done, focusing on what the change claims and on the public-repo rules.
---

Use before handing off or committing a change.

1. Read the diff for scope creep: anything outside the task's files goes back out or into docs/FOLLOWUPS.md.
2. Check the diff for keys, tokens, recordings, tester names or private files. The repo is public.
3. Run the project's checks (`python tools/verify.py` once it exists; until then the tests and the headless Godot check). A tool you couldn't run makes the claim unverified, not green.
4. Exercise the exact thing that changed: the analyzer on the sample session, the build with the add-on, or the report page in a browser with a screenshot.
5. Check that the report page computes nothing and that every model call went through the client.
6. At a milestone, check the quality bar in AGENTS.md, "When to switch to more Claude", line by line, with evidence for each.
7. Report:
   - the files changed;
   - what a user would see differently;
   - the commit, the commands and where the evidence is;
   - the credits used so far;
   - what you didn't check.

Don't add broad tests or tooling just to satisfy this list.
