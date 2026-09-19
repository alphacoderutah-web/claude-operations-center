---
id: repository-wide-secret-scan
title: "validate scans every text file in the repository, this brain included, for credential-, card- and SSN-shaped text"
category: concept
status: active
tags: [safety, validate, secrets]
created: "2026-09-18T18:07:48"
updated: "2026-09-18T18:07:48"
---

<!-- compiled_truth -->
## Definition

`ops.py validate` checks the records (T-1). It also walks the **whole repository**, not just `registry/` and `state/`, and reports an error on any line that looks like a secret or sensitive number:

- **Scope.** Every file with a text suffix (`.md`, `.json`, `.jsonl`, `.py`, `.txt`, `.ps1`, `.sh`, `.cmd`, `.toml`, `.yml`, `.yaml`), skipping `.git`, `__pycache__`, `node_modules`, `.venv` and the git-ignored `evidence/` folder.
- **Credential shapes.** Well-known provider key and token prefixes (Anthropic, GitHub, AWS, Slack, Google, live payment keys), PEM private-key headers, and an assignment of a long value to a name like password, secret, api key or token.
- **Card numbers.** 13 to 19 digits, optionally separated, that pass the Luhn checksum and are not a single repeated digit, so ordinary long numbers pass.
- **SSN shapes.** The standard three-two-four digit pattern.

## Why it is this way

- Records must hold only references to credentials and never personal data (README safety model; BOOTSTRAP ground rules). Scanning every text file catches a leak wherever it lands: a procedure, a note, a project CLAUDE.md template, or this brain.
- `evidence/` is exempt because it is git-ignored raw survey output that never leaves the machine.
- `publish` runs `validate` before committing, and CI runs `validate --no-paths` on every push and pull request, so the public template is scanned too.

## Boundaries and consequences

- **It is a shape check, not a secret detector.** Prose that mentions a token passes; a long value assigned to a secret-like name fails. A test pins exactly this.
- **The repository must pass its own scan.** A test (`test_this_repository_is_clean`) scans the checkout. The scanner's own test samples are assembled at runtime so that the test file itself stays clean.
- **This brain is in scope.** Brain pages in the template and in every company copy must never contain a credential-like assignment, a Luhn-valid card-length number or an SSN-shaped number, even as an example. Describe such patterns in words, as this page does ([[brain-describes-the-template]]).

Related: [[test-suite-runs-in-every-copy]].


## Timeline

- time: 2026-09-18T18:07:48
  kind: decision
  summary: "Created this page: validate scans every text file in the repository, this brain included, for credential-, card- and SSN-shaped text"
  source: "tools/ops.py scan_for_secrets; tests/test_ops.py SecretScanTests; CI"
  affects: [repository-wide-secret-scan]

- time: 2026-09-18T18:07:48
  kind: decision
  summary: "captured from tool, tests and CI"
  source: "tools/ops.py SECRET_PATTERNS, CARD_RE, SSN_RE, SCANNED_SUFFIXES, SCAN_SKIP_DIRS, scan_for_secrets; tests/test_ops.py SecretScanTests; .github/workflows/tests.yml"
  affects: [repository-wide-secret-scan]
