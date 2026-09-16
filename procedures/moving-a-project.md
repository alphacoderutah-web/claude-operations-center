# Moving or renaming a project folder

A project's path is written into far more places than its own code. Projects are identified by
their registry `id`, so after a move only the `path` fields change in the registry. Everything
else has to be found and fixed.

## Before the move

1. Find every reference to the old path, in every spelling: backslashes, forward slashes,
   doubled backslashes, `//c/…`-style, and the Claude transcript folder name (`C--Old-Path`).
   Look in:
   - OS scheduled jobs, their arguments and working folders, and the wrapper scripts they call
   - Claude routine prompts, and each routine's stored working folder and permission rules
   - global and project Claude settings (`additionalDirectories`, allow rules)
   - other projects' code and config (`depends_on` lists the known ones)
   - generated launchers, virtual-environment files and console-script shims, Git worktrees, and
     `node_modules` links
   - any exclusion list keyed by folder name. Such lists fail open on a rename, so check them first.
2. Check for open Claude sessions inside the folder, because they lock it.
3. Stop the project's scheduled work.

## The move

4. On Windows, move with `[System.IO.Directory]::Move(old, new)`. It moves the whole tree or
   throws with nothing touched. `Move-Item` can fall back to per-file moves when the folder is
   locked, and split the tree.

## After the move

5. Re-point everything found in step 1. Then regenerate path-bound launchers and shims.
   - A desktop app that holds routine settings in memory may rewrite its file while running.
     Change those settings only with the app closed.
   - A routine whose working folder no longer exists may silently never start.
6. Update `path` in `registry/projects.json`, then run `ops.py validate` and `render`.
7. Verify each job from its own evidence: trigger or wait for one run, then read its result.
   Confirm that routines started in the new folder and did not stall at a permission prompt.
8. Copy any relevant per-folder Claude memory, which does not follow the folder.
9. Record the move with `ops.py record`.
