---
name: operations-center
description: Set up or run a company operations center from this repository — bootstrap a new company (interview, read-only machine survey, registry, company-wide Claude instructions, private publish), register a new project, record status and work, or pause a project's automations during an incident. Use when asked to set up the operations center, onboard a company, add a project to the registry, check company status, or record what was done.
---

# Operations center

Read `ops.config.json` first.

- **`template.bootstrapped` is false:** follow `BOOTSTRAP.md` stage by stage. The survey is
  read-only; `procedures/baseline-survey.md` and `procedures/survey-agent-prompts.md` describe it.
  Ask the owner one question at a time.
- **`template.bootstrapped` is true:** follow `procedures/daily-operations.md`. Start with
  `python tools/ops.py status`.
  - New projects: `procedures/new-project.md`.
  - Incidents: `procedures/pausing-automations.md`.
  - Changes going live: `procedures/maintenance-and-release.md`.

Never read credential values, never put personal data in the records, and never push company
records to the public template (`ops.py publish` enforces this).
