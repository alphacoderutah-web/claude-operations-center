# Claude Operations Center

A template that turns one folder into the **operations center** for a company run with
[Claude Code](https://code.claude.com). Clone it into the company workspace, and a Claude agent
follows the playbook to build:

- **one registry** of every project, scheduled job, business asset, external system and credential
  reference the company depends on
- **company-wide instructions** that every Claude session loads (interactive sessions, projects,
  unattended routines), deferring to each project's stricter rules
- **dated status that goes stale honestly**: an observation past its time-to-live reads as
  *unknown*, never as its last good value
- **a prioritized work queue** and an append-only **decision log** and **history**
- **procedures** for the recurring hard parts:
  - starting a project
  - releasing changes safely
  - renewing sign-ins
  - moving folders
  - pausing jobs during an incident
- **one small standard-library tool** (`tools/ops.py`) that validates, renders, records and
  publishes all of it

Every company's projects, settings, goals and processes differ. The structure, the safeguards and
the method stay the same.

## Quick start

1. Choose a company workspace, for example `C:\Company` or `~/company`, with projects in
   `Projects/`.
2. Clone this repository into it as `ops`:
   ```bash
   git clone https://github.com/alphacoderutah-web/claude-operations-center.git ops
   ```
3. Open Claude Code in `ops` and say:
   > Set up this operations center for our company. Follow BOOTSTRAP.md.

Claude will then work through the bootstrap stages:

1. Make the company's copy private.
2. Interview you, one question at a time.
3. Survey the machine, read-only.
4. Write the registry, status and queue.
5. Install the company instructions and verify they load.
6. Publish to the company's private repository.

It stops only for the things that need you: decisions, sign-ins and approvals.

## How it works

```text
<workspace>/
├── ops/                         ← this repository (the company's private copy)
│   ├── ops.config.json          company name, time zone, business functions, install target
│   ├── instructions/company.md  company-wide Claude instructions → installed to ~/.claude/CLAUDE.md
│   ├── COMPANY.md               what the business does, entities, people, systems, priorities
│   ├── PROJECTS.md              generated index of projects, automations, dependencies
│   ├── registry/                projects, automations, assets, systems, access references (JSON)
│   ├── state/                   observations, queue, decisions, history
│   ├── procedures/              bootstrap survey, daily operations, new project, release, access,
│   │                            moving, pausing
│   ├── templates/               starter files for new projects and for init
│   ├── tools/ops.py             the tool
│   └── evidence/                raw survey output (git-ignored)
├── Projects/
│   ├── <project A>/             each project keeps its own code, CLAUDE.md and repository
│   └── <project B>/
└── …
```

| Command (run in `ops/`) | What it does |
|---|---|
| `python tools/ops.py init --company "Name" --timezone Area/City` | Configure this copy for a company |
| `python tools/ops.py status` | Current observations (stale ones read UNKNOWN) and open work |
| `python tools/ops.py validate` | Check every record; reject credential-shaped text, card numbers, SSNs |
| `python tools/ops.py render` | Regenerate `PROJECTS.md` |
| `python tools/ops.py new-project --id … --name … --function … --purpose …` | Register a project and create its starter folder |
| `python tools/ops.py observe …` / `record …` | Record a dated observation / a history line |
| `python tools/ops.py pause --project ID [--apply]` | Show or apply the pause steps for a project's jobs |
| `python tools/ops.py install [--check]` | Install the company instructions where Claude Code loads them |
| `python tools/ops.py publish -m "…"` | Validate, render, test, commit and push (never to this template) |

A worked example for a fictional company is in [`examples/harborline-bakery`](examples/harborline-bakery).

## Safety model

- **Written rules are the real gate.** Unattended sessions may run with permission checks off, so
  the instructions require explicit owner approval before any of these, unless a project's written
  standing authorization covers the exact action:
  - moving money
  - sending messages
  - publishing or deploying to production
  - deleting data
  - changing credentials or access
  - accepting terms
- **Projects can be stricter.** The instructions defer to each project's own `CLAUDE.md`, and
  company instructions never widen what an unattended job may do.
- **No secrets, no personal data.** The records hold where a credential lives and how it is
  renewed, never its value. `validate` fails on credential-shaped text. The survey never opens
  credential files.
- **Company data stays private.** `publish` refuses to push while `origin` is this public
  template, and bootstrap moves the template to a separate `template` remote first.
- **Evidence over assertion.** A scheduler's "succeeded" is not proof; status records name their
  evidence and expire.

## Design choices

- **The records live in a subfolder (`ops/`), not at the workspace root.** A repository at the
  root would enclose every project folder. Backup scanners that stop at the first `.git` would
  treat the workspace as one project, and commit hooks would sweep unversioned projects into it.
- **The instructions install at user level by default.** `~/.claude/CLAUDE.md` loads in every
  session, including company projects outside the workspace, without import approvals. On a
  shared machine, set `instructions.install_to` to `<workspace>/CLAUDE.md` instead.
- **JSON records, generated views.** A future daily email and dashboard read exactly what Claude
  reads.

## Requirements

- Claude Code (CLI, desktop app or IDE)
- Python 3.10+ and Git
- The GitHub CLI (`gh`), optional, for creating the private repository
- Windows, macOS or Linux. The survey covers Task Scheduler, cron, launchd, systemd and Claude
  routines. `pause --apply` changes Windows tasks; other schedulers show their registered manual
  step.

## Recommended companion skills

The template's default `standing_skills` in `ops.config.json`:

- [agency-conduct](https://github.com/alphacoderutah-web/agency-conduct-skill): an operating
  standard for autonomous work, covering verification, approval locks and one-action handoffs.
- [drive-the-task](https://github.com/alphacoderutah-web/drive-the-task-skill): drive portal and
  form work to the final screen, stopping only at real gates.

Install them into `~/.claude/skills/`, or change `standing_skills` to your own.

## Updating a company copy from the template

```bash
git -C ops fetch template
git -C ops merge template/main
python ops/tools/ops.py validate
```

Template changes touch the tool, procedures, templates and tests, never a company's records.

## Development

```bash
python -m unittest discover -s tests -t tests
```

Keep the template generic: no company names, real identifiers, personal data or machine-specific
paths. See [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
