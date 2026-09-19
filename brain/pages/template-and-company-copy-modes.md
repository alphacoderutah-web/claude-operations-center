---
id: template-and-company-copy-modes
title: "One repository, two modes: template.bootstrapped decides whether this is the public template or a company's records"
category: decision
status: active
tags: [template, config, modes]
created: "2026-09-18T18:06:53"
updated: "2026-09-18T18:07:08"
---

<!-- compiled_truth -->
## What was decided

The same repository is both the public template and, after `ops.py init`, one company's private operations records. A single flag, `ops.config.json` → `template.bootstrapped`, says which one a given copy is:

| | `false`: the template | `true`: a company copy |
|---|---|---|
| Agent entry point (`CLAUDE.md`, the operations-center skill) | Follow `BOOTSTRAP.md` stage by stage | Follow `procedures/daily-operations.md`; start with `ops.py status` |
| Records | Empty skeletons. A template-only test checks that no projects ship and that the empty registry renders its hint | The company's registry and state |
| `ops.py publish` | Refused ("not initialized for a company") | Allowed, unless `origin` is the template (T-8) |
| `validate` | No instructions-drift check | Also warns when the installed instructions differ from `instructions/company.md` |
| PROJECTS.md currency test | Skipped (nothing generated yet) | Enforced |
| Improving the template itself | Keep it generic: no company names, real identifiers, personal data or machine-specific paths | Not applicable. Template improvements come from upstream ([[template-upgrade-by-merge]]) |

`init` is the only transition. It fills the company name, time zone, workspace, functions and install target, sets `bootstrapped = true`, writes `instructions/company.md` and `COMPANY.md` from `templates/`, renders `PROJECTS.md` and records the event in history.

## Why

- One clone gives a company everything: the tool, procedures, templates, tests and a place for its records. There is no separate generator step.
- The agent needs an unambiguous signal of which playbook applies. A flag in the config it reads first is that signal.
- Refusing to publish an uninitialized copy stops template skeletons being pushed as if they were company records, and the T-8 guard covers the opposite direction.

## Blast radius

- Anything added to the template must make sense in both modes, and must not assume company data exists.
- Tests that exercise the tool build scratch workspaces and never read the copy's own records ([[test-suite-runs-in-every-copy]]).
- Content that describes the template, such as this brain, also lands in company copies ([[brain-describes-the-template]]).


## Timeline

- time: 2026-09-18T18:06:53
  kind: decision
  summary: "Created this page: One repository, two modes: template.bootstrapped decides whether this is the public template or a company's records"
  source: "ops.config.json, CLAUDE.md, operations-center skill, tools/ops.py"
  affects: [template-and-company-copy-modes]

- time: 2026-09-18T18:06:54
  kind: decision
  summary: "captured from config, CLAUDE.md, skill and tool"
  source: "ops.config.json template.bootstrapped; CLAUDE.md; .claude/skills/operations-center/SKILL.md; tools/ops.py initialize and cmd_publish; tests/test_records.py"
  affects: [template-and-company-copy-modes]

- time: 2026-09-18T18:07:08
  kind: decision
  summary: narrow the skeleton-test claim to what the test checks
  source: tests/test_ops.py TemplateSkeletonTests
  affects: [template-and-company-copy-modes]
