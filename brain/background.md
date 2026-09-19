---
slug: background
title: Project background
role: project background
updated: "2026-09-18T18:05:25"
---

# Project background

## About this brain

This brain describes the **template**: the design of the operations-center template itself, its tool, its procedures and the reasoning behind them. It holds no company's facts.

The template is copied wholesale into each adopting company's private operations repository, so this brain travels with it. A company copy may **keep** it as the template's design record, or **remove** it during bootstrap. See [[brain-describes-the-template]] for what each choice involves. Company facts and decisions belong in the company's own records (`COMPANY.md`, `registry/`, `state/`), never in this brain.

## Why

A company run with Claude Code accumulates projects, scheduled jobs, credentials, external systems and rules spread across many folders. Without one place that knows all of them, every session starts blind, status goes stale silently, and unattended jobs can act beyond what anyone wrote down. The template turns one folder into the company's **operations center**: a registry of everything the company depends on, company-wide instructions every Claude session loads, dated status that expires honestly, a work queue, a decision log and history, and procedures for the recurring hard parts. A Claude agent builds it for a new company by following `BOOTSTRAP.md`.

Per `CHANGELOG.md` (1.0.0), the template was generalized from an operations center already in use.

## Goals

- **Same structure, any company.** Every company's projects and processes differ; the structure, the safeguards and the method stay the same (README).
- **One small, dependency-free tool** (`tools/ops.py`, Python standard library) that initializes, validates, renders, records, pauses and publishes.
- **Written rules as the real gate.** Unattended sessions may run with permission checks off, so the installed instructions carry the approval limits and never widen them.
- **Honest status.** An observation past its time-to-live reads as unknown.
- **Safe by construction.** No secrets or personal data in the records, a validator that rejects credential-shaped text, and a publish step that refuses to push company records to the public template.
- **Agent-run bootstrap.** Stop for the owner only for decisions, sign-ins and approvals, and ask one question at a time.

## Non-goals

- Holding any company's data in the template itself. The shipped registry and state are empty skeletons, and the worked example is fictional.
- Storing credential values anywhere. The records hold references and renewal steps only.
- Replacing each project's own rules. Company instructions defer to stricter project rules.
- Changing schedulers other than Windows Task Scheduler automatically. `pause --apply` changes Windows tasks only; other schedulers get their registered manual step.
- Building a daily email or dashboard. The design anticipates them (views generated from the same JSON), but neither ships.

## Target user

- **The owner** of a small or mid-sized company that runs its operations with Claude Code, on Windows, macOS or Linux.
- **The Claude agent** that bootstraps and then maintains the company's copy, following `BOOTSTRAP.md`, the procedures and the operations-center skill.
- **Template maintainers** improving the template itself, who must keep it generic ([[template-and-company-copy-modes]]).

## Canonical records

- `state/decisions.md`, entries **T-1 to T-8**: the template's framework design decisions. This brain links to them and does not restate them.
- `CHANGELOG.md`: release history.
