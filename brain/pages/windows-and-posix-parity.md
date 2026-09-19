---
id: windows-and-posix-parity
title: "Windows and POSIX are both first-class: CI on both, LF everywhere, one resolved path spelling"
category: decision
status: active
tags: [portability, windows, ci]
created: "2026-09-18T18:08:01"
updated: "2026-09-18T18:08:02"
---

<!-- compiled_truth -->
## What was decided

The template runs on Windows, macOS and Linux (README), and the tool is written so that the same records produce the same bytes on every platform:

- **CI matrix.** Ubuntu and Windows, with Python 3.10 (the stated minimum) and 3.13. The workflow runs the test suite and `validate --no-paths` (added in 1.0.1). macOS is claimed in the README but is not in CI.
- **LF everywhere.** `.gitattributes` sets `* text=auto eol=lf` because the tool compares generated files byte for byte (`render --check`, the PROJECTS.md currency tests, the instructions drift check). Every file the tool writes uses `newline="\n"`.
- **One path spelling.** `load_context()` resolves the repository root once, so every path the tool writes uses one spelling. On Windows a temporary or user folder can have an 8.3 short name, and before 1.0.1 generated instructions mixed short and long spellings of the same folder. The first Windows CI run found it (commit fccb17c). The tests' scratch workspaces resolve their paths the same way.
- **UTF-8 output.** `main()` reconfigures stdout to UTF-8, so Windows consoles print the tool's em dashes and arrows.
- **Scheduler reach.** `pause --apply` drives Windows Task Scheduler through PowerShell. On other systems it prints the registered manual step, and it reports a skip rather than failing silently when run off Windows.

## Why

- The playbooks are Windows-heavy in places (Task Scheduler, DPAPI checks for signed-out browser jobs, safe folder moves), but a company may run on any OS. Byte-for-byte checks are only trustworthy if every platform writes the same bytes.
- CI on Windows exists because Windows is where the path and line-ending bugs appear. The first run proved it.

## Alternatives

None are recorded in the repository.

## Blast radius

- New generated output must be written with LF and from resolved paths, or the currency tests will fail on one platform.
- Adding automatic pause support for another scheduler means a new branch in `cmd_pause` and tests that run on that OS.

Related: [[test-suite-runs-in-every-copy]].


## Timeline

- time: 2026-09-18T18:08:01
  kind: decision
  summary: "Created this page: Windows and POSIX are both first-class: CI on both, LF everywhere, one resolved path spelling"
  source: "git log bde2e68 and fccb17c; .gitattributes; .github/workflows/tests.yml; tools/ops.py"
  affects: [windows-and-posix-parity]

- time: 2026-09-18T18:08:02
  kind: decision
  summary: "captured from 1.0.1 commits, CI and tool"
  source: "git log bde2e68 (CI, 1.0.1) and fccb17c (8.3 short-name fix); .gitattributes; .github/workflows/tests.yml; tools/ops.py load_context, write_json, cmd_pause; README Requirements"
  affects: [windows-and-posix-parity]
