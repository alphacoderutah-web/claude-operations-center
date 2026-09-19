---
id: test-suite-runs-in-every-copy
title: "The test suite ships with every copy: tool tests use scratch workspaces, record tests guard whichever records the copy holds"
category: decision
status: active
tags: [tests, template, safety]
created: "2026-09-18T18:08:18"
updated: "2026-09-18T18:08:33"
---

<!-- compiled_truth -->
## What was decided

The tests are not only the template's development suite. They run inside every company copy, because `ops.py publish` runs them before it commits. The suite is therefore split by what it may read.

- **Tool tests (`tests/test_ops.py`)** build a scratch, uninitialized company workspace in a temporary folder and copy only `templates/` into it. The `Workspace` docstring says why: in a company copy, the repository's own config and records are the company's real data. They cover init, validation, the secret scan, views and staleness, new-project scaffolding, install and drift, the publish guard (including every URL form of the template remote), and pause planning. There are two deliberate exceptions:
  - template skeleton checks load the repository's own config and skip themselves when the copy is bootstrapped;
  - the self-scan runs the secret scan over the checkout, and reports only file and line, never the matched text ([[repository-wide-secret-scan]]).
- **Record tests (`tests/test_records.py`)** validate whichever records the copy holds. In the template, that is the empty skeleton plus the worked example. In a company copy, they guard the company's real records, so an invalid record or a stale `PROJECTS.md` fails the tests, and `publish` refuses.
- **The worked example is a fixture.** `examples/` holds a complete, fictional company. Tests require it to validate with no errors, its `PROJECTS.md` to match a fresh render, and its instructions to be fully filled (no leftover placeholders). A company copy may delete the example; those tests then skip.

## Why

- A company copy needs the same safety net as the template, at the moment it matters most: right before its records are committed and pushed.
- Tool tests that read real records could leak company data into test output, or fail on legitimate company content, so they are isolated by construction.
- A realistic example that must stay valid catches schema or renderer changes that the empty skeleton would never exercise.

## Blast radius

- A template change to the tool or schema must keep the example valid and its `PROJECTS.md` current, or CI fails.
- After a template merge, a company's publish re-runs the whole suite against its own records ([[template-upgrade-by-merge]]).
- Run the suite with `python -m unittest discover -s tests -t tests`. CI runs it on Ubuntu and Windows ([[windows-and-posix-parity]]).

Related: [[template-and-company-copy-modes]].


## Timeline

- time: 2026-09-18T18:08:18
  kind: decision
  summary: "Created this page: The test suite ships with every copy: tool tests use scratch workspaces, record tests guard whichever records the copy holds"
  source: "tests/test_ops.py Workspace; tests/test_records.py; tools/ops.py cmd_publish"
  affects: [test-suite-runs-in-every-copy]

- time: 2026-09-18T18:08:18
  kind: decision
  summary: captured from test design and publish
  source: "tests/test_ops.py (Workspace docstring, suites); tests/test_records.py docstring; tools/ops.py cmd_publish; .github/workflows/tests.yml"
  affects: [test-suite-runs-in-every-copy]

- time: 2026-09-18T18:08:33
  kind: decision
  summary: state the two deliberate exceptions to scratch-workspace isolation
  source: tests/test_ops.py TemplateSkeletonTests and test_this_repository_is_clean
  affects: [test-suite-runs-in-every-copy]
