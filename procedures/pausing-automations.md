# Pausing automations during an incident

Use this when a job is doing harm, or could do harm, while a problem is investigated.

## 1. Pause what writes, then investigate

Pause in this order, and stop at the first group that covers the incident:

1. Jobs that move money, message customers, or control physical access.
2. Jobs that change public content or external records.
3. Everything else, one project at a time.

```bash
python tools/ops.py pause --project <project-id>            # show the plan
python tools/ops.py pause --project <project-id> --apply    # stop and disable its Windows tasks
```

Other schedulers print their registered manual pause step (`pause` in
`registry/automations.json`). Tasks that run while nobody is signed in may need an elevated
shell. Pausing is reversible; deleting a job is not a pause. Prefer a project's own kill switch
when it has one.

## 2. Record it

```bash
python tools/ops.py observe <project-id>-incident --subject <project-id> --status failing --statement "Paused because …" --evidence "<log path>" --ttl-hours 24
```

Add the incident to `state/queue.json`. When one cause breaks several projects (an expired
sign-in, a lost credential store), record **one** incident that names them all.

## 3. Resume

Resume only after the cause is fixed and verified by the job's own health check or a dry run.

```bash
python tools/ops.py pause --project <project-id> --resume --apply
```

Then confirm the first real run from its log, and close the incident with what was affected and
what the job had already done. Never replay completed external actions.
