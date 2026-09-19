---
id: brain-describes-the-template
title: "This brain records the template's design only; a company copy keeps it as that record or removes it at bootstrap"
category: decision
status: active
tags: [template, brain, bootstrap, scope]
created: "2026-09-18T18:06:41"
updated: "2026-09-18T18:06:41"
---

<!-- compiled_truth -->
## What was decided

This brain (`BRAIN.md`, `brain/` and the marked brain block in `CLAUDE.md`) describes the **operations-center template**: its design, its tool, its procedures and why they are the way they are. It holds no company's facts, and the template rule in `CLAUDE.md` applies to it in full: no company names, real identifiers, personal data or machine-specific paths.

Because a company adopts the template by cloning the whole repository, the brain arrives in every company copy. The company chooses one of two options during bootstrap.

### Option 1: keep it as the template's design record

- Treat it as read-mostly reference on why the template works as it does.
- Put company facts and decisions in the company's own records: `COMPANY.md`, `registry/`, `state/`, and D-numbered entries in `state/decisions.md`. Keep them out of this brain, so that template upgrades can update the brain cleanly ([[template-upgrade-by-merge]]).
- Reading or writing the brain needs the brain skills and their CLI on the machine. The brain block in `CLAUDE.md` assumes they are installed.

### Option 2: remove it

Remove `BRAIN.md`, the `brain/` folder, the block between `<!-- BEGIN brain.md -->` and `<!-- END brain.md -->` in `CLAUDE.md`, and the two brain lines in `.gitattributes`. Later template merges that change those files will show as modify/delete conflicts. Resolve them by keeping the deletion. (That follows from how Git merges; it has not been exercised yet.)

## Why

- The template's own design reasoning otherwise lives only in `state/decisions.md` (T-1 to T-8), `CHANGELOG.md` and commit messages. The brain gathers the rest, such as mode switching, the upgrade path, portability and test design, and links to those canonical records instead of restating them.
- A company's operations records already have a complete, validated structure for company knowledge. A second, unvalidated place for company facts would split the truth.

## Blast radius

- `ops.py validate` scans every text file in the repository, including this brain, in the template and in every company copy ([[repository-wide-secret-scan]]). Brain pages must never contain credential-, card- or SSN-shaped text.
- `BOOTSTRAP.md` does not yet mention the keep-or-remove choice. That is an open question in the roadmap.

Related: [[template-and-company-copy-modes]].


## Timeline

- time: 2026-09-18T18:06:41
  kind: decision
  summary: "Created this page: This brain records the template's design only; a company copy keeps it as that record or removes it at bootstrap"
  source: "CLAUDE.md template rule; repository layout"
  affects: [brain-describes-the-template]

- time: 2026-09-18T18:06:41
  kind: decision
  summary: scope of the template brain and the keep-or-remove choice for company copies
  source: "CLAUDE.md (keep the template generic); README (updating a company copy); brain adoption 2026-09-18"
  affects: [brain-describes-the-template]
