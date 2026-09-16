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
