# Company: Harborline Bakery Co.

Created 2026-09-16. This is how the business is organized. Structured facts live in `registry/`,
and anything that changes day to day lives in `state/`. Where sources disagree, record the
conflict instead of choosing a side.

<!-- Fill each section during bootstrap (BOOTSTRAP.md, stage 3), from the owner and from evidence.
     Keep personal data minimal: roles, not home addresses or personal phone numbers. -->

## What the business does

A two-store bakery with a commissary kitchen. It sells retail at both stores and supplies wholesale customers (cafes and grocers) by next-morning delivery.

## Entities and brands

| Entity or brand | Role |
|---|---|
| Harborline Bakery Co. | Operating company; holds both stores, the kitchen and the wholesale accounts. |

## Assets

What the business operates (properties, locations, vehicles, products, client accounts). The full
list, with every system's identifier, is in `registry/assets.json`.

## People and responsibilities

| Who | Responsibilities |
|---|---|
| Owner | Decides and approves protected actions; receives alerts. |
| Head baker | Receives the daily production plan. |
| Store managers | Maintain item availability in the POS by hand. |
| Claude | Runs the projects' automations and maintenance within each project's written authority, keeps these records current, and hands the owner one action at a time. |

## Systems of record

A short summary; the full list is in `registry/systems.json`.

## Recurring obligations

| When | What |
|---|---|
| Daily 16:00 | Next-day production plan |
| Monthly, 1st | Review replies |
| Annually | Food-service permit renewals, per location |

## Operating priorities

In order:

1. Anything harming customers or money right now.
2. Obligations with dates (filings, renewals, expiring sign-ins).
3. Unfinished work already started.
4. Improvements, taken from the queue.

## Standing owner preferences

- Time zone for dates and schedules: America/New_York.
