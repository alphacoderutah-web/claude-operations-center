# Maintenance and release

How a change moves from a found problem to a verified live result. Each project's own rules still
govern its operational writes: payments, messages, edits to external systems, and filings.

## The cycle

1. **Identify.** Record the issue, its evidence, the affected projects (use `depends_on` and
   `shared_surfaces`) and the authority that applies. Queue it if it will not be finished now.
2. **Change and check.** Make the smallest change in the component that owns the behavior, and
   run checks proportional to its impact.
3. **Commit** to the project's own repository.
4. **Deploy.** Deploy automatically only when the change is **routine** and the project's registry
   entry has `release.deploy_authority: "auto"`. Otherwise, prepare the deploy and ask the owner.
5. **Confirm live.** Check the result at the layer that matters: a live request, a fresh job run,
   or the served page. Record the deployed version in history, and update the observation.
6. **Recover** if the live check fails. Roll back to the recorded previous version. Never replay
   external actions the failed version already took; the project's ledger is the record.

## Routine or not

A change is **routine** only when it does none of the following:

- changes how money is charged, refunded, paid or reported, or any limit or allowlist
- changes the wording, recipients or triggers of messages to customers, staff, partners or
  authorities
- widens what a job may write in an external system, or adds a new external write
- touches credentials, access, authentication or security controls
- deletes or migrates persistent data, or changes a schema
- changes production traffic, DNS or routing
- creates an external commitment: an account, subscription, filing or purchase
- reverses a recorded decision or a project's standing rule

When in doubt, it is not routine.

## Checks

| Impact | Minimum checks before deploy |
|---|---|
| Documentation or records only | `ops.py validate`; a secret scan of the diff |
| Code with tests | The full suite, plus the lint and type checks the project already runs |
| Code without tests | Reproduce the failure, then show the same path succeeding; a dry run where one exists |
| Deployed service | The above, plus the build, then a live check |
| Anything that writes externally | The above, plus a dry run or read-back through the project's own gates |

Record which checks ran. A check that did not run is reported as not run.

## Commit hooks

If the machine uses a hook that commits and pushes at the end of each Claude turn:

- Anything not ignored can be committed, so make private data ignored before working in a
  repository.
- A hook that merges into the default branch bypasses review. Projects whose live service runs
  from that branch need a per-repository policy (queue it).
- Folders with no repository of their own are not versioned by the hook.

## Shared components

Before changing a component other projects depend on (the `depends_on` entries pointing at it),
check it against every consumer. Skills and global settings affect every session: change the
authoritative copy, then install it, and keep a dated backup of global settings.
