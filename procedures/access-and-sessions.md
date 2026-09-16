# Access, sign-ins and saved sessions

Expired sign-ins are a common single point of failure for automations that drive web apps.
`registry/access.json` records, for each service:
- where its credential or session lives (a reference, never a value)
- its copies
- which jobs depend on it
- how it is renewed
- how failure is detected

`state/observations.json` holds the last time each one was checked.

## Two kinds of browser

| Browser | Used for | Who signs in |
|---|---|---|
| The owner's everyday browser, driven by Claude (for example Claude in Chrome), with the owner's password manager | Interactive work, and routines that read what the owner already sees | Already signed in; the owner handles prompts |
| Automation profiles, each owned by one job (Playwright persistent profiles or saved session files) | Unattended jobs | The owner signs in once, inside that profile, when the job's login command opens it |

Never sign in, sign out or clear data in a profile another job owns.

## When a job reports it is signed out

1. **Check the machine first.** If several browser-based jobs lose their sessions together, or a
   session is lost again right after renewal, the operating system may be failing to protect
   browser data.
   - On Windows, test per-user DPAPI across two separate processes: protect a value in one
     PowerShell process and unprotect it in a new one. Then count
     `Microsoft-Windows-Crypto-DPAPI/Operational` event 8198.
   - A known fix, when the account signs in with Windows Hello only: turn off *Only allow Windows
     Hello sign-in for Microsoft accounts*, sign out completely, and sign in with the password.

   A new sign-in will not stick until this is fixed.
2. **Consolidate.** Find every job that depends on the same service and account, and ask the
   owner once, for all of them.
3. **Make it one action.** Open the job's own login command on the sign-in page, and ask the
   owner to sign in and say when the dashboard is visible. Never type or ask for a password, code
   or recovery key.
4. **Verify the account, not the message.** Run the job's own health check with a fresh browser
   launch, and confirm it is signed in to the right account.
5. **Resume from the last confirmed step.** Use the job's ledger. Never redo a completed external
   write.
6. **Record it** with `ops.py observe`, including any expiry the service shows.

## Git hosting credentials

If git uses a credential helper backed by the OS credential store, losing that store breaks every
push, often silently for scheduled pushes. Re-authenticate with the hosting CLI's device or web
flow (for example `gh auth login --web`), and have the owner complete it in the browser.

## Rules

- Keep secrets out of instructions, reports, logs and Git. Record locations and renewal steps.
- Prefer a supported API credential over a browser session wherever the service offers one.
- Unattended jobs need credentials that work without the owner present. Password-manager autofill
  is not such a mechanism.
- Copies of one secret in many files make rotation error-prone. Record every copy, and
  consolidate them over time.
