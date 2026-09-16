# Baseline survey

A read-only inventory that tells the operations center what actually exists and runs. Repeat it
after any large change, such as a folder move, a new machine or an incident, and at least
quarterly.

## Rules

- Change nothing:
  - no task edits, runs or restarts
  - no logins, builds or deploys
  - no `git fetch`, `pull`, `commit` or `push`
  - no project scripts that contact external services
- Never open credential material: `.env*`, `.dev.vars`, keys, cookie databases, browser profile
  contents, saved-session JSON, token files or credential stores. Record path, size and modified
  time only. Learn variable *names* from the code that loads them.
- Never copy personal data into the output. Refer to records by ID, date or amount.
- Write only inside `evidence/<date>-baseline/`, which is git-ignored.

## What to collect

| Area | Collect | Where to look |
|---|---|---|
| Projects | Every folder under the projects directory, plus projects elsewhere that the company depends on. For each: what it is, whether it has Git, its remote and visibility, commits ahead or behind, uncommitted and untracked counts, last commit, CI, `CLAUDE.md` and README presence, and whether `.gitignore` covers `.env` | File system; `git status`, `git log`, `git remote -v`; `gh repo view --json visibility` |
| Scheduled jobs | Every non-system job: action, arguments, working folder, triggers, whether it runs with nobody signed in, last run and result, next run, and whether every path it uses exists | Windows: `Get-ScheduledTask`, `Get-ScheduledTaskInfo`, exported XML, wrapper scripts. macOS: `launchctl list`, `~/Library/LaunchAgents`. Linux: `crontab -l`, `systemctl --user list-timers`. Claude routines: `~/.claude/scheduled-tasks/*/SKILL.md` and the desktop app's routine registry. Cloud: wrangler, serverless or CI configs with schedules |
| Run history | Recent successes and failures, from each job's own logs or ledgers | Project `logs/`, ledgers and SQLite databases (open them read-only) |
| Claude configuration | Global and project settings (permissions, additional directories, hooks); installed skills and whether each is versioned; every `CLAUDE.md`; routine prompts; standing authorizations with file:line | `~/.claude/`, project `.claude/` folders |
| Rule conflicts | Where a project rule contradicts or narrows the company defaults (approvals, browser choice, deploys, commit and push behavior) | The files above |
| Access | For each service a job signs in to: mechanism, where the credential or session lives, copies, dependent jobs, renewal steps, failure detection, and the last success or failure seen in logs | Code that loads credentials; runbooks; logs; secret-scanner findings (names and fingerprints only) |
| Notifications | Every email, SMS, chat or push message a job sends: channel, trigger, recipients (role or business address), content type | Code and config |
| Platform | Power and sleep settings, recent reboots and unexpected shutdowns, OS-level health that affects saved sessions (on Windows, a per-user DPAPI test across two processes) | `powercfg`, event logs, `last`/`uptime` |
| Assets | Each list of assets kept by a project, and where the lists disagree | Project config and data maps |
| Earlier reports | Every claim in an older survey or handoff, marked open, resolved, changed or unverifiable, with evidence | The report, then current evidence |

## Recording a finding

```json
{"id": "short-slug", "project": "…", "claim": "…", "current_status": "open|resolved|changed|unverifiable",
 "evidence": [{"path": "…", "line_or_record": "…", "observed": "…", "observed_at": "ISO time"}],
 "checked_at": "ISO time with offset", "notes": "direct evidence vs inference"}
```

Keep direct evidence and inference apart. A scheduler's "succeeded" is not proof that the job did
its work. Read the job's own report.

## Turning findings into records

The findings feed BOOTSTRAP.md stage 5:

- Each project becomes a registry entry, and each scheduled job an automation.
- Each credential or session becomes an access record.
- Each asset list becomes a set of asset sources.
- Each open finding becomes an observation, or a queue item when it needs action.

Verified-good states become `ok` observations. Stale evidence is left out rather than presented
as current.
