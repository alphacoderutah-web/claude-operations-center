# Changelog

## 1.0.0 — 2026-09-16

First public release, generalized from a working operations center for a multi-property rental
business.

- `tools/ops.py`: init, validate (with credential, card-number and SSN scanning), render, status
  with expiring observations, new-project scaffolding, observe, record, pause, install, and
  publish with a guard against pushing company records to the template.
- Registry schema: projects, automations, assets, systems (including shared write surfaces) and
  access references.
- State: observations, work queue, append-only decisions and history.
- `BOOTSTRAP.md` playbook, plus procedures for the baseline survey (with sub-agent prompts),
  daily operations, new projects, maintenance and release, access and sessions, moving projects,
  and pausing automations.
- A worked example company (`examples/harborline-bakery`) and a test suite.
