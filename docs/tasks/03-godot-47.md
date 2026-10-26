# 03: Open COGITO in Godot 4.7.2

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, working directly in `game/` on `playtest-lens` (no worktree, Sasha's rule for Godot tasks).
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** this repo at the commit named in the prompt; `game/` at `676be6d` on branch `playtest-lens`.

## Goal

One outcome: `game/` holds exactly the Godot 4.7.2 editor's own rewrite of the 4.6 project, ready for the orchestrator to commit on `playtest-lens` as "Open in Godot 4.7.2".

Sasha (T3 Code chat, 2026-10-26): "one commit on playtest-lens, “Open in Godot 4.7.2”, holding only the editor's own rewrite. Check the diff has no content changes".

Task 02 saw the rewrite: 261 tracked files, `project.godot` `config/features` from `4.6` to `4.7`, and new keys in `.import` files (for example `mesh_library/use_node_names_as_mesh_names`, `array_mesh/deduplicate_surfaces`, `gltf/texture_map_mode` in `barrel.glb.import`).

## Files you own

The tracked files in `game/` that Godot itself rewrites. Write nothing by hand in `game/`, and nothing outside it.

## What to do

1. Check `git -C game status --short` is empty and `git -C game rev-parse HEAD` is `676be6dd6f412c87b391b51593bc4bb356571630` on branch `playtest-lens`. If not, stop and report.
2. Import headless with the standard build only: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --import`. Save the output to `runs/checks/03-import-1.log`.
3. Import a second time, output to `runs/checks/03-import-2.log`, and check the second import changed nothing more (compare `git -C game diff --stat` before and after).
4. Run the main scene briefly: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --quit-after 600`, output to `runs/checks/03-run.log`. Compare its errors with task 02's `runs/checks/02-run.log`.
5. Classify the diff (`git -C game diff`):
   - by file type, with counts (`project.godot`, `*.import`, anything else);
   - every kind of changed line, with one example hunk each;
   - anything that is not an editor format rewrite: a `.tscn`, `.tres`, `.gd`, `.gdshader`, asset or `.uid` change, a changed value (not a new key), a removed line. List each one. Don't revert or edit it; the orchestrator decides.

## Done means

- The two imports exit 0, and the second adds no change.
- The classified diff in your report, with every non-format change listed (or "none").

## Report back

The commands with exit codes, the diff classification, the log paths, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Only `/Applications/Godot.app/Contents/MacOS/Godot`, never `Godot_mono.app`.
- Don't commit, don't push, don't change branches, remotes, submodule or LFS settings.
- No em dashes or spaced en dashes in anything you write.

## What came back

Grok 4.7, one run. Two headless imports exit 0 and the second adds nothing; the 600-frame run matches task 02's errors (exit cleanup only, and COGITO's headless input-icon message). The diff: 261 files, `project.godot` and 260 `.import` files, 781 lines added, 1 removed. Logs: `runs/checks/03-*.log` (not in the repo).

## What the orchestrator changed

Nothing in the files. Recounted every changed line: 260 times each `+array_mesh/deduplicate_surfaces=true`, `+gltf/texture_map_mode=0` and `+mesh_library/use_node_names_as_mesh_names=false`, and `config/features` from `4.6` to `4.7`. No content change. Committed on the fork's `playtest-lens` as `de772aa` "Open in Godot 4.7.2" and pushed it; the fork's `main` stays at `676be6d`.
