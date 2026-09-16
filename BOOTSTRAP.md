# Bootstrap: setting up an operations center for a company

This is the playbook a Claude Code agent follows after cloning this repository for a new company.
The result is a company workspace with one folder that knows every project, automation, asset,
system and credential reference, plus the following:

- company-wide instructions that every Claude session loads
- dated status that goes stale honestly
- a prioritized work queue
- a decision log
- procedures for the recurring hard parts

Work in stages. Finish each stage's check before starting the next.

## Ground rules for the whole bootstrap

- **Read-only until stage 5.** The survey observes and writes only inside this repository and its
  git-ignored `evidence/` folder. It does not change tasks, services, projects or accounts.
- **Never read secrets.** Record where a credential lives, never its value. Do not open `.env`
  files, cookie stores, session files or token files.
- **Keep personal data out.** Customer, staff and owner details stay out of the records. Use
  roles and system IDs.
- **Ask the owner only what only the owner knows.** Ask one question at a time, and propose a
  default when there is a sensible one.
- **Company records never go to the public template.** `ops.py publish` refuses while `origin`
  points at the template.

## Stage 1: Place the repository

1. Choose the company workspace: the folder that holds, or will hold, the company's projects.
   For example `C:\Company` or `~/company`, with projects in `Projects/` inside it.
2. Clone this repository into the workspace as `ops`:
   ```bash
   git clone https://github.com/alphacoderutah-web/claude-operations-center.git ops
   ```
   The records live in a subfolder, not at the workspace root, deliberately. A repository at the
   root would enclose every project folder. Backup scanners and commit hooks would then treat
   unversioned projects as part of it, and projects with their own repositories as nested noise.

**Check:** `python ops/tools/ops.py --help` runs, using Python 3.10 or newer.

## Stage 2: Make the company's copy private

1. Rename the template remote so company records can never be pushed to it:
   ```bash
   git -C ops remote rename origin template
   ```
2. Create a **private** repository for the company, with the owner's approval, and make it
   `origin`. With the GitHub CLI:
   ```bash
   gh repo create <owner>/<company>-ops --private --source ops --remote origin
   ```
3. Later template improvements can be merged from `template` deliberately
   (`git fetch template && git merge template/main`).

**Check:** `git -C ops remote -v` shows `origin` as the private repository, and `gh repo view`
reports `PRIVATE`.

## Stage 3: Learn the company from the owner

Ask the owner, one question at a time, and propose defaults. Stop once you have enough to start.
The survey fills in the rest.

1. Company name, and the time zone to use for dates and schedules.
2. What the business does, for whom, and where.
3. Legal entities and brands, and which accounts belong to which.
4. The business functions to group projects by. Offer the defaults in `ops.config.json` and
   adjust.
5. People and roles: who approves what, who receives alerts, and who works on site.
6. Systems of record: where the truth lives for customers, money, inventory or listings,
   compliance, and so on.
7. Standing rules:
   - what Claude may do unattended
   - what always needs approval
   - anything another team owns
8. How the owner wants reports: channel, time and recipient. Record it as a decision now, even if
   it will be built later.

Then initialize:

```bash
cd ops
python tools/ops.py init --company "Company Name" --timezone America/Chicago \
  --function operations="Operations" --function money="Money" ...
```

`init` writes `ops.config.json`, `instructions/company.md`, `COMPANY.md` and an empty
`PROJECTS.md`. Fill `COMPANY.md` from the answers, and add the owner's standing rules to the
"Company-wide rules" section of `instructions/company.md`. Record each owner decision in
`state/decisions.md`, using the owner-decision form described there.

**Check:** `python tools/ops.py validate` reports 0 errors.

## Stage 4: Survey the machine (read-only)

Follow `procedures/baseline-survey.md`. In short, inventory:

- every project folder and Git repository (remote, visibility, unpushed or uncommitted work)
- every scheduled or always-on job (Windows Task Scheduler, cron, launchd, systemd, Claude
  routines, cloud schedulers), including whether each one runs with nobody signed in, whether the
  paths it uses exist, and its last result
- Claude Code configuration: settings, hooks, installed skills, `CLAUDE.md` files, standing
  authorizations, and any conflicts between them
- credentials and saved sessions (locations and renewal steps only), plus every notification a
  job sends
- the assets the business operates, and every list of them held in different projects
- older reports or notes, each claim re-checked against current evidence

Parallel read-only sub-agents make this fast. `procedures/survey-agent-prompts.md` has prompts
that work. Raw output goes to `evidence/<date>-baseline/`, which is git-ignored.

**Check:** every project folder and every scheduled job appears in the evidence.

## Stage 5: Write the records

1. `registry/projects.json`: one entry per project, with:
   - a permanent `id`, `function`, `classification` and `lifecycle`
   - `purpose`, `path` and `repo`
   - `systems` (with read/write/charge/send modes) and `depends_on`
   - `automations` and `writes`
   - `authority`: the written rule that governs its external writes, with file:line
   - `release` (`deploy_authority` stays `owner` unless a written rule says otherwise)
   - `recovery`
2. `registry/automations.json`: one entry per job, with:
   - `kind`, `cadence`, `runs_signed_out` and `needs_browser`
   - `writes` and `access`
   - `pause`: the quickest safe way to stop it
3. `registry/systems.json`: the authoritative systems, plus `shared_surfaces` for every external
   field more than one job writes.
4. `registry/access.json`: every credential or session, with where it lives, its copies, the jobs
   that depend on it, how it is renewed, and how a failure is detected.
5. `registry/assets.json`: each asset, with its identifiers in every system and every
   disagreement between sources.
6. `state/observations.json`: current status per subject, each with `checked_at`, `evidence` and
   `ttl_hours`.
7. `state/queue.json`: every problem found, ranked P1–P4, with an owner and a `next_step`. Put
   decisions only the owner can make here too.
8. `state/history.jsonl`: record the survey (`ops.py record`).

Then run `python tools/ops.py validate` and `python tools/ops.py render`.

**Check:** 0 errors, and `PROJECTS.md` lists every project.

## Stage 6: Install the company instructions

1. Review `instructions/company.md`. Keep it short: every Claude session loads it, including
   unattended ones. It must never widen what an unattended job does.
2. `python tools/ops.py install` copies it to `~/.claude/CLAUDE.md` (configurable). That file
   loads in every session on the machine, including projects outside the workspace, with no
   import approvals. If the machine is shared with unrelated work, set `instructions.install_to`
   to `<workspace>/CLAUDE.md` instead, and accept that projects outside the workspace will not
   see it.
3. Verify that a **new** session loads it. Either:
   - run `claude -p "Quote the first heading of your company instructions" --tools ""` from a
     project folder (with hooks disabled if your hooks commit), or
   - create a temporary manual-only Claude routine that reports its loaded instruction files,
     run it once, read the result, and delete it.

**Check:** a new session quotes the company instructions' heading.

## Stage 7: Publish

```bash
python tools/ops.py publish -m "Create the company operations records"
```

`publish` validates, renders, runs the tests, commits and pushes. It refuses to push to the
template.

**Check:** the private repository shows the commit.

## Stage 8: Report to the owner

Start with the single most urgent action the owner must take, then summarize:

- what exists now
- what was verified, and how
- what could not be verified
- the P1 and P2 items in the queue, and the decisions waiting on the owner

## After bootstrap

- `procedures/daily-operations.md`: how every later session uses the records.
- `procedures/new-project.md`: adding a project.
- Natural next stages, each recorded as a queue item:
  - a scheduled read-only health check that refreshes observations
  - a daily email and a dashboard generated from `state/`
  - a per-repository commit policy
  - consolidating copied credentials
