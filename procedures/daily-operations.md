# Daily operations

How any Claude session uses the operations center after bootstrap.

## Starting company work

1. `python tools/ops.py status` (from `ops/`) shows current observations (stale ones read
   **UNKNOWN**) and open work by priority.
2. Before changing a project, read its registry entry in `PROJECTS.md` and its own `CLAUDE.md`.
3. Before touching an external field, check `registry/systems.json` → `shared_surfaces` for other
   writers.

## Choosing what to do

Work in this order:

1. incidents
2. items with dates
3. work already in progress
4. P1–P2 improvements

Owner decisions and sign-ins are `owner` items. Prepare everything around them, then ask for one
thing at a time.

## Finishing work

1. `python tools/ops.py record --subject <id> --summary "…" --evidence <path>`
2. `python tools/ops.py observe <id> …` for any status you re-checked, with a `ttl_hours` that
   matches how fast it changes:

   | How often it changes | ttl_hours |
   |---|---|
   | Hourly jobs | 3 |
   | Daily jobs | 26 |
   | Configuration | 168 |

3. Update `state/queue.json`. Close items with a note; never delete them.
4. Update the registry when purpose, path, dependencies, automations or access change.
5. `python tools/ops.py publish -m "…"`

## Unattended routines

Routines report through their own channel and do not edit company records. A scheduled,
read-only health check is the right way to refresh observations automatically. When built, it
belongs in this repository's `tools/`, runs on a scheduler that needs no sign-in, and writes only
observations.

## Reporting to the owner

- Lead with the single action the owner must take, if any.
- Then give what changed, what was verified and how, and what remains.
- A daily email or dashboard reads `state/observations.json` and `state/queue.json`, so what it
  shows is exactly what the records say, including what is unknown.
