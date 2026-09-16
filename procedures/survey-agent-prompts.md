# Survey agent prompts

Run these as parallel, read-only sub-agents during the baseline survey. Replace the placeholders:

| Placeholder | Meaning |
|---|---|
| `<WORKSPACE>` | The company workspace |
| `<PROJECTS>` | Its projects folder |
| `<OUTSIDE>` | Company projects that live elsewhere |
| `<EVIDENCE>` | `ops/evidence/<date>-baseline` |
| `<DATE>` | Today |
| `<TZ>` | The company time zone |

Every prompt starts with the same hard rules.

## Shared rules (prepend to every prompt)

```text
You are doing a READ-ONLY baseline inventory for a company's operations machine. Today is <DATE> (<TZ>).
HARD RULES:
- Change nothing:
  - do not create, edit, enable, disable, run or stop tasks, services, routines or files
  - do not run project scripts, builds, logins, deploys or tests
  - git: status, log, rev-parse, remote -v, branch -vv, for-each-ref, rev-list, worktree list,
    ls-files and check-ignore only; no fetch, pull, commit or push
- Never open .env*, .dev.vars, keys, cookie databases, browser profile contents, saved-session
  files, token files or credential stores. Record path, size and mtime only. Learn variable NAMES
  from the code that loads them.
- Never copy personal data into your output; refer to records by id, date or amount.
- Open SQLite read-only (file:PATH?mode=ro).
- Write only inside <EVIDENCE>.
- Distinguish direct evidence from inference. State only what you observed.
```

## 1. Automations

```text
Inventory every scheduled or always-on job: OS schedulers (Windows Task Scheduler outside
\Microsoft\, cron, launchd, systemd timers), Claude routines (~/.claude/scheduled-tasks/*/SKILL.md
and the desktop app's routine registry, read-only), cloud schedules in wrangler/serverless/CI
files under <PROJECTS> and <OUTSIDE>, and services or startup items that run project code.

For each job record:
- action, arguments, working folder and triggers in plain words
- whether it runs with nobody signed in, and whether it needs a browser
- last run, last result (with its meaning), next run
- whether every path it uses exists, including paths inside the wrapper scripts it calls

Rebuild recent run history from each job's own logs if the scheduler keeps none. Also record the
power and sleep settings and recent reboots.

Write <EVIDENCE>/automations.json and reply with a table plus a problems list.
```

## 2. Repositories and backups

```text
For every folder in <PROJECTS> and <OUTSIDE>, and every git repository up to 5 levels below them
(skip node_modules, .venv, dist), record:
- path, branch and default branch
- remotes, GitHub name and visibility (gh repo view)
- ahead/behind against the last-fetched remote refs (note when that fetch was)
- modified and untracked counts, last commit
- CI; CLAUDE.md, README and .claude/settings presence
- whether .gitignore covers .env

For folders with no git: file count, size, newest file, what the folder holds.

Also find how any backup scanner in use discovers projects, and whether a repository at
<WORKSPACE> would change that.

Write <EVIDENCE>/repos.json and reply with a table plus problems: no remote, unpushed work,
public repositories holding private data, unignored secrets, redundant worktrees.
```

## 3. Claude configuration and rules

```text
Inventory Claude Code configuration:
- ~/.claude/settings.json (permissions, additionalDirectories, hooks) and every project
  .claude/settings*.json
- installed skills: versioned or not, plus duplicates and drift between copies
- every CLAUDE.md or AGENTS.md
- routine prompts and their stored permission rules (read-only)

List every standing authorization with file:line and date. Compare the project rules against
these company defaults, and list each contradiction with file:line:
- no money movement, sending, publishing, production deploys, deletion or credential entry
  without approval, unless a written standing authorization covers it
- the owner's chosen default browser
- drive portal work yourself, one human action at a time
- routine changes deploy automatically within existing limits
- any commit or push hook's behavior

Write <EVIDENCE>/claude-config.md and reply with the skill table, rule summaries,
authorizations and conflicts.
```

## 4. Access, sessions and notifications

```text
For every job and project, list each external service it authenticates to:
- mechanism, and where the credential or session lives (reference only)
- copies of the same secret (a secret scanner's fingerprints can show these)
- dependent jobs
- renewal steps (file:line), failure detection, and the last success or failure seen in logs

For browser-based jobs, record profile paths and cookie-file metadata only.

Platform checks:
- OS sign-in method
- on Windows: Windows Hello status, the "only allow Windows Hello sign-in" setting, a two-process
  DPAPI test, and recent DPAPI error counts
- credential-manager target names (not values)
- which browser profiles hold the password-manager extension
- CLI sign-in status for git hosting and cloud tools

Also list every notification a job sends: channel, trigger, recipients as role or business
address, content type, and file:line.

Write <EVIDENCE>/access.json and reply with tables plus problems.
```

## 5. Findings by business area (one agent per area)

```text
Verify the claims in <REPORT OR HANDOFF> for these projects: <LIST>, against current local
evidence: logs, ledgers, git history, configs. For each claim, record id, project, claim,
current_status (open, resolved, changed or unverifiable), evidence and checked_at. Put
time-sensitive items (deadlines, sign-in expiries) first.

For assets these projects track: build a reconciled table of each asset's identifiers per source
and where the sources disagree. Use identity fields only; no personal names.

For external fields more than one job writes: list each writer, the field, its cadence and any
coordination between them.

Write <EVIDENCE>/findings-<area>.json and reply with the findings table.
```
