---
slug: mindmap
title: Feature mindmap
role: feature mindmap
updated: "2026-09-18T18:06:12"
---

# Feature mindmap

## Feature mindmap

```mermaid
mindmap
  root((Operations center template))
    Registry
      Projects with permanent IDs
      Automations with pause steps
      Assets and source conflicts
      Systems and shared surfaces
      Access references, never values
    State
      Observations with time-to-live
      Ranked work queue
      Append-only history
      Decision log
    Instructions
      Company template
      Install to user level
      Drift check
      Defer to stricter project rules
    Playbooks
      Bootstrap stages 1 to 8
      Baseline survey and agent prompts
      Daily operations
      New project
      Maintenance and release
      Access and sessions
      Moving a project
      Pausing automations
    ops.py
      init
      validate and secret scan
      render and status
      new-project
      observe and record
      pause
      install
      publish with template guard
    Template mechanics
      Template or company-copy mode
      Upgrade by merging the template remote
      Worked example as fixture
      CI on Windows and Ubuntu
```

Decisions behind the branches: T-1 to T-8 in `state/decisions.md`; [[template-and-company-copy-modes]], [[template-upgrade-by-merge]], [[repository-wide-secret-scan]], [[windows-and-posix-parity]], [[test-suite-runs-in-every-copy]], [[brain-describes-the-template]].
