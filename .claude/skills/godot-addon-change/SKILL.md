---
name: godot-addon-change
description: Change the Godot logging add-on or its COGITO adapter, keeping it passive, testable headless and limited to the fork's playtest-lens branch.
---

Use for the add-on, the adapter, or the fork's branch.

1. The general add-on knows nothing of COGITO: inputs, scene changes, player position by node path, the start flash and beep. COGITO-only events (pickups, doors, keypads, quest steps) go in the adapter.
2. Listen and write; never change gameplay, timing, input or saves. The adapter connects to COGITO's signals and edits none of COGITO's scripts beyond wiring the add-on in.
3. Every line is JSON with a timestamp from one clock, the same one the start flash marks, so the video and the log line up.
4. Commit fork changes only on its `playtest-lens` branch, and list each one in docs/PRIOR_WORK.md.
5. Check it headless: a Godot run of a test scene that fires the events and checks the lines written. Then launch the real demo, do the action, and show the log lines it wrote.
6. Run the `validate-change` skill.

Headless success doesn't prove the start flash or the beep: check those in the running game, with a screenshot.
