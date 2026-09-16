# Starting a new project

## The short way

1. Open Claude in the company workspace.
2. Say what you want, for example: *"New project: a weekly inventory report for each store. It
   reads the point-of-sale system and changes nothing."* Include:
   - what it should do
   - what it covers
   - what it may change
3. Answer Claude's questions. Claude follows the steps below and stops only for approvals,
   sign-ins and creating repositories.

---

## Step 1: Check it isn't already covered

Look in `ops/PROJECTS.md` for a project that already does this, or nearly does. Reuse what exists:
- asset identifiers from `registry/assets.json`
- shared code other projects already depend on
- credentials already recorded in `registry/access.json`

## Step 2: Register it and create its folder

From the `ops` folder:

```bash
python tools/ops.py new-project --id inventory-report --name "Inventory Report" --function operations --purpose "Builds a weekly inventory report for each store."
```

- `--id` is permanent: lowercase with hyphens.
- `--function` is one of the business functions in `ops.config.json`.

The command creates `<workspace>/Projects/Inventory Report` with a starter `CLAUDE.md` and
`.gitignore`. It never overwrites existing files. It also registers the project, updates
`PROJECTS.md` and records the history.

## Step 3: Write the project's rules

Fill in the project's `CLAUDE.md`:

- **Reads:** what it reads.
- **Writes:** every external change it may make.
- **Approval:** what the owner approves, and any standing permission (with limits and date).
- **Personal data:** where it is kept (git-ignored).
- **Credentials:** where they live (a reference only) and how they are renewed.
- **Deploy:** how a change goes live.

This file is what keeps an automated job inside its limits.

## Step 4: Back it up

1. Check that `.gitignore` covers secrets and personal data.
2. Run `git init`.
3. Create a **private** repository with the owner's approval, and push.

## Step 5: Complete the registry entry

In `registry/projects.json`, fill in these fields:
- `repo`
- `systems`, with modes
- `depends_on` and `writes`
- `authority`, pointing to the written rule
- `release`, with `deploy_authority` left as `owner` until the owner decides otherwise
- `recovery`

Then update the related registry files:
- `registry/access.json`: every credential or session the project uses
- `registry/systems.json` → `shared_surfaces`: add it wherever it writes a field another job
  also writes
- `registry/assets.json`: if the project keeps its own asset list, record that list as a source

## Step 6: Schedule it (only if it runs on its own)

1. Create the scheduled job.
   - Use a scheduler that runs while nobody is signed in when the job must never wait for a
     sign-in.
   - Use a Claude routine when it needs Claude or the owner's browser.
2. Register it in `registry/automations.json`, with its cadence, whether it runs signed out,
   which browser it needs, what it writes and **how to pause it**. List it under the project's
   `automations`.
3. Make sure the job reports failures, not only successes.

## Step 7: Prove it works

1. Do a dry run, then one real run. Read the job's own result, not just the scheduler's status.
2. Record it:
   ```bash
   python tools/ops.py observe inventory-report-first-run --subject inventory-report --status ok --statement "First run built 6 store reports" --evidence "<path to output>" --ttl-hours 168
   ```
3. Move `lifecycle` from `pilot` to `live` or `scheduled` once the project runs reliably.

## Step 8: Publish

```bash
python tools/ops.py publish -m "Register inventory-report"
```

## Checklist

- [ ] Checked `PROJECTS.md` for an existing project
- [ ] `new-project` run
- [ ] Project `CLAUDE.md` filled in
- [ ] Secrets and personal data ignored; private repository pushed
- [ ] Registry entry, access and shared fields recorded
- [ ] Automations registered with a pause step and a failure alert
- [ ] First run verified and recorded
- [ ] `publish` run
