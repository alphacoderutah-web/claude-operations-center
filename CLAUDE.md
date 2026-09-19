# Operations center repository

This repository is either the public **template** or one company's private **operations
records**. Check `ops.config.json` → `template.bootstrapped`:

- **`false`: you are setting up a new company.** Follow `BOOTSTRAP.md` stage by stage. Ask the
  owner one question at a time, keep the survey read-only, and never push company data to the
  template remote.
- **`true`: this is a company's records.** The company-wide rules are in
  `instructions/company.md` (installed for every session). Inside this repository:
  - Edit `registry/*.json` and `state/*.json` by hand or with `tools/ops.py observe | record |
    new-project`. Never hand-edit `PROJECTS.md`; run `python tools/ops.py render`.
  - After any change, run `python tools/ops.py validate` and
    `python -m unittest discover -s tests -t tests`. Publish with
    `python tools/ops.py publish -m "…"`.
  - `state/decisions.md` and `state/history.jsonl` are append-only.
  - Every observation needs `checked_at`, `evidence` and `ttl_hours`. Report only what the
    evidence shows.
  - `evidence/` is git-ignored raw evidence. Keep it for a limited time (90 days is a sensible
    default), then delete it.
  - Never put secrets, or customer, staff or owner personal data, anywhere in this repository.
  - After changing `instructions/company.md`, run `python tools/ops.py install`. Only sessions
    started afterwards load the new text.

When improving the template itself (not a company copy), keep it generic: no company names, real
identifiers, personal data or machine-specific paths. Run the tests before committing.

The project brain below describes the template itself, never a company. Reading or writing it
needs the brain.md skills (github.com/mindmuxai/brain.md). A company copy may keep it as the
template's design record or remove it during bootstrap; see
`brain/pages/brain-describes-the-template.md`.

<!-- BEGIN brain.md -->
## Project Brain

This project keeps a **Project Brain**: a persistent memory layer of its durable decisions, requirements, and constraints. Read `./BRAIN.md` for the full read/write contract.
@import ./BRAIN.md

The `brain` CLI is not guaranteed to be on `PATH`. From the project root, invoke it as `node <brain-page-skill-dir>/bin/brain.mjs <subcommand> [flags]`, resolving `<brain-page-skill-dir>` to the installed `brain-page` skill directory.

Maintain the brain as part of normal coding work — not as a separate task. While discussing or implementing features:
- **Start of a task:** load relevant context with the `brain` CLI (`list-pages`, `read-page`, `read-root`). Prefer a narrow read over scanning everything.
- **When a decision, requirement, constraint, or durable insight settles** (in chat or while coding): capture it immediately via the `brain` CLI. Do not wait to be asked and do not batch it for later.
- **Pure implementation with no new decision:** do not write to the brain.
- **When overturning a prior conclusion:** update the page (`update-truth` and/or `append-timeline` with `kind: reversal`, or `archive-page`).
- Only store what will still matter in six months and is hard to reconstruct from the code alone.
- Never hand-edit brain files. If a brain MCP server is connected and authenticated, prefer it; otherwise use the `brain` CLI.

The brain skills (`brain-setup`, `brain-page`, `brain-ingest`, `brain-bootstrap`) are installed in your global skills directory. To scaffold a new project, run `node <brain-page-skill-dir>/bin/brain.mjs init` from its root.
<!-- END brain.md -->
