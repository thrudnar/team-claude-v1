# Job Hunting Portfolio — Future Roadmap

This file captures deferred ideas and "consider for later" improvements across the four job hunting projects. Items here are not scheduled work — they are candidates for future planning cycles.

Active work items live in each project's own `plan.md`.

---

## Projects in scope

| # | Project | Active plan |
|---|---------|-------------|
| 1 | Job Listing Harvester | `Projects/Job Listing Harvester/plan.md` |
| 2 | Job Description Match Score | `Projects/Job Description Match Score/` |
| 3 | Application Workflow | `Projects/Application Workflow/plan.md` |
| 4 | Gmail Monitoring | `Projects/Gmail Monitoring/` |

---

## Ideas backlog

### UI for managing the `interesting_companies` table

**Area:** Project 3 — Application Workflow / UI (Iris)

Companies are currently added to `interesting_companies` via direct SQL as a one-off step. A dedicated UI view would make the table usable without CLI or DB access.

**What it would cover:**
- Add, edit, and view entries in `interesting_companies`
- Expose the table's rich fields: interest drivers, apprehensions, size, sector, culture, evilness rating, and any other metadata columns
- These fields exist in the schema but are effectively unused today because there is no accessible way to populate them

**Why it matters:** The table is designed to inform smarter targeting and cover letter tone. Its value is locked behind the barrier of raw SQL access.

**Consider for:** Future Iris sprint, likely alongside or after Application Workflow v2 ships.

---
