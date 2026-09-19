---
id: template-upgrade-by-merge
title: "Company copies take template improvements by merging a template remote; template changes never touch company records"
category: decision
status: active
tags: [template, upgrade, git]
created: "2026-09-18T18:07:20"
updated: "2026-09-18T18:07:33"
---

<!-- compiled_truth -->
## What was decided

A company copy keeps the public template as a Git remote named `template` (bootstrap stage 2 renames the original `origin`). It takes improvements by fetching and merging `template/main`, then running `ops.py validate`. There is no separate installer or update command.

The rule that makes this work (README): **template changes touch the tool, procedures, templates and tests, never a company's records.**

## How the file split supports it

| Owned by the template (changes arrive by merge) | Owned by the company after bootstrap |
|---|---|
| `tools/`, `procedures/`, `templates/`, `tests/`, `BOOTSTRAP.md`, `README.md`, `CHANGELOG.md`, the skill, CI, `examples/` | `instructions/company.md`, `COMPANY.md`, `PROJECTS.md`, `registry/*.json`, `state/observations.json`, `state/queue.json`, `state/history.jsonl` |

The template ships the record files as empty skeletons and, under the rule above, leaves them alone afterwards.

Two files are shared, and they deserve care (inferred from the layout; neither case has been exercised yet):

- **`ops.config.json`** ships with template defaults and is rewritten by `init` with company values. An upstream change to its defaults would meet the company's edits in a merge.
- **`state/decisions.md`** carries the template's framework decisions T-1 to T-8, and a preamble telling companies to keep them and to number their own decisions from D-001. Template entries and company entries sit in separate parts of the file.

## Why

- Git is already required, and a merge keeps the company's full history alongside every upstream change.
- The same remote naming gives T-8 its guard: `publish` compares `origin` with the configured template URL, so a company's pushes can only go to its private repository.

## Blast radius

- A template change that edits a company-owned file, or changes the record schema, breaks this contract. Every file carries `schema_version: 1`, but no migration path exists yet (roadmap open question).
- Content added to the template, including this brain, reaches every company copy on the next merge ([[brain-describes-the-template]]).
- After a merge, the company's own tests re-validate its records against the new tool ([[test-suite-runs-in-every-copy]]).

Related: [[template-and-company-copy-modes]].


## Timeline

- time: 2026-09-18T18:07:20
  kind: decision
  summary: "Created this page: Company copies take template improvements by merging a template remote; template changes never touch company records"
  source: "README (Updating a company copy), BOOTSTRAP.md stage 2, state/decisions.md preamble"
  affects: [template-upgrade-by-merge]

- time: 2026-09-18T18:07:20
  kind: decision
  summary: "captured from README, BOOTSTRAP.md and decisions preamble"
  source: "README 'Updating a company copy from the template'; BOOTSTRAP.md stage 2; state/decisions.md preamble; tests/test_records.py"
  affects: [template-upgrade-by-merge]

- time: 2026-09-18T18:07:33
  kind: decision
  summary: "mark merge-conflict expectations as inferred; note ops.config.json is shared"
  source: review against README and tools/ops.py initialize
  affects: [template-upgrade-by-merge]
