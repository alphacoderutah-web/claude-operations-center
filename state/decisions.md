# Decisions

Append-only. Each entry says who decided, when, and what it changes. Record a reversal as a new
entry. Owner decisions are authoritative; design decisions can be revisited.

Owner decisions use this form:

```markdown
## D-001 · <short title> · owner · <YYYY-MM-DD>

<What was decided and what it changes.>
Source: <conversation, document or message>.
```

The framework decisions below come with the template. Keep them unless the owner decides
otherwise, and number company decisions from D-001.

---

## T-1 · Records are JSON; views are generated · design

The registry (`registry/*.json`) and operating state (`state/observations.json`,
`state/queue.json`, `state/history.jsonl`) are JSON. `PROJECTS.md`, the status view, any daily
email and any dashboard are generated from them, so every view agrees. `tools/ops.py` validates
the records, including a scan for credential-shaped text, and uses only the Python standard
library.

## T-2 · Stable identifiers · design

Every project has a permanent lowercase `id`. Automations use `<kind-prefix>:<native name>`.
Cross-references use IDs, never paths, so a folder move changes only `path` fields.

## T-3 · Status expires · design

Every observation carries `checked_at`, evidence and `ttl_hours`. After its time-to-live it reads
as **unknown**, never as its last value. Subjects with no observation read as unknown.

## T-4 · The records live in `<workspace>/ops`, not at the workspace root · design

A repository at the workspace root would enclose every project folder. Backup scanners that stop
at the first `.git` would treat the whole workspace as one project. Commit hooks would sweep
unversioned project folders into the operations repository. A subfolder repository avoids both.

## T-5 · Company instructions are installed at user level by default · design

`instructions/company.md` is the canonical text. `ops.py install` copies it to
`~/.claude/CLAUDE.md`, which loads in every session on the machine: the workspace, every project,
unattended routines, and company projects outside the workspace. Only one copy exists, and no
import approvals are needed. A machine shared with unrelated work can install to
`<workspace>/CLAUDE.md` instead.

## T-6 · Instructions stay short and never widen unattended scope · design

Every session loads the company instructions, including unattended ones that may run with
permission checks off. They therefore carry only standing rules and pointers, defer to stricter
project rules, and never grant new write authority. Skills are named, not copied. Naming a skill
guides the model; it does not grant it tool permissions.

## T-7 · Unattended sessions do not edit company records · design

Scheduled routines report through their own channels and stay within their project's scope.
Interactive sessions, and a dedicated read-only health check, update the records.

## T-8 · Company records never reach the public template · design

The template repository is public. `ops.py publish` refuses to push while `origin` is the
template, and bootstrap renames that remote to `template` before the company's private repository
becomes `origin`.
