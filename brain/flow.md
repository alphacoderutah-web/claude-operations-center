---
slug: flow
title: Key flows
role: key flows
updated: "2026-09-18T18:05:56"
---

# Key flows

## End-to-end path of a typical request

**Bootstrap: from a fresh clone to a company's private operations center** (`BOOTSTRAP.md`, stages 1 to 8). Each stage ends with a check that must pass before the next begins.

```mermaid
sequenceDiagram
  participant O as Owner
  participant A as Claude agent
  participant R as ops/ (this repo)
  participant M as Machine (read-only survey)
  participant G as Git hosting
  A->>R: 1. clone into the workspace as ops/
  A->>R: 2. rename origin to template
  A->>O: approve creating a private repository?
  A->>G: create private repo, set it as origin
  A->>O: 3. interview, one question at a time
  A->>R: ops.py init (config, instructions, COMPANY.md, PROJECTS.md; bootstrapped = true)
  A->>M: 4. baseline survey via parallel read-only sub-agents
  M-->>R: raw output to evidence/ (git-ignored)
  A->>R: 5. write registry, observations, queue, history
  A->>R: validate + render
  A->>R: 6. ops.py install (instructions to the install target)
  A->>A: verify a NEW session loads the instructions
  A->>R: 7. ops.py publish
  R->>R: refuse if not bootstrapped or origin is the template
  R->>R: validate, render, run tests
  R->>G: commit and push to the private origin
  A->>O: 8. report: most urgent owner action first
```

## Other important flows

- **Daily operations** (`procedures/daily-operations.md`). `status` first, where stale observations read UNKNOWN. Work in order: incidents, dated items, work in progress, then P1 to P2 improvements. Finish with `record`, `observe` (with a time-to-live matched to how fast the subject changes), queue updates and `publish`. Unattended routines report through their own channel and leave the records unchanged (T-7).
- **New project** (`procedures/new-project.md`). `new-project` validates the entry and scaffolds a folder with a starter `CLAUDE.md` and `.gitignore` (never overwriting). The agent then writes the project's rules, backs it up privately, completes the registry, registers any automation with a pause step, proves a first run, and publishes.
- **Incident pause** (`procedures/pausing-automations.md`). `pause --project` prints the plan and changes nothing. `--apply` stops and disables that project's Windows tasks; other schedulers print their registered manual step. Pause order: jobs that move money, message customers or control physical access first.
- **Release** (`procedures/maintenance-and-release.md`). A change deploys automatically only when it is routine **and** the project's registry entry has `deploy_authority: "auto"`. The procedure lists what makes a change non-routine.
- **Template upgrade into a company copy.** Fetch and merge the `template` remote, then validate ([[template-upgrade-by-merge]]).
