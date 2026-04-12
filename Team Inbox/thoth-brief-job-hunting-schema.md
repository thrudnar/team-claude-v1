# Schema Design Brief — Job Hunting Portfolio

**From:** Adama
**To:** Thoth
**Date:** 2026-03-31

---

## Context

The owner is building a job hunting portfolio of 4 linked projects. Read `Projects/Job Listing Harvester/context/portfolio-overview.md` for the full picture. This brief covers the cross-project schema design.

The database is the integration layer between all four projects. Design for clean handoffs between projects via well-managed state.

---

## Tables Required

### `jobs` — cross-project, owned by Harvester

The central table. One row per job listing. Unique on `(job_board, job_id)`.

Fields from owner's existing spreadsheet:
- `id` — PK
- `job_board` — TEXT (LinkedIn, BuiltIn, Jobright, career page, etc.)
- `job_id` — TEXT (source platform's ID)
- `company` — TEXT
- `job_title` — TEXT
- `location` — TEXT
- `work_type` — TEXT (remote / hybrid / onsite)
- `job_url` — TEXT
- `description_text` — TEXT (full page content, stored at harvest time — do not fetch live at scoring time)
- `first_date_seen` — TEXT
- `most_recent_date_seen` — TEXT
- `source_email_id` — TEXT (nullable, for future email-sourced listings)
- `is_new` — INTEGER DEFAULT 1
- `status` — TEXT (harvester status: new / reviewed / skipped / applied)
- UNIQUE constraint on `(job_board, job_id)`

### `job_scores` — owned by Match Score project

One row per scored job. Linked to `jobs`. Includes a `score_version` field because the scoring prompt will evolve and re-scoring must be traceable.

Fields:
- `id` — PK
- `job_id` — FK to jobs
- `score_version` — TEXT (identifier for which prompt version was used)
- `overall_score` — INTEGER (0–100)
- `skills_score` — INTEGER (0–100)
- `seniority_score` — INTEGER (0–100)
- `work_type_score` — INTEGER (0–100)
- `match_summary` — TEXT
- `strengths` — TEXT
- `gaps` — TEXT
- `cover_letter` — TEXT (generated for high-match jobs)
- `resume_customizations` — TEXT (recommendations for tailoring resume)
- `scored_at` — TEXT

State management: a job should only be scored once per score_version. The absence of a `job_scores` row (or a row with a different version) is what triggers scoring.

### `applications` — owned by Application Workflow project

One row per application submitted. Linked to `jobs` where possible.

Fields:
- `id` — PK
- `job_id` — FK to jobs (nullable — some applications may predate the harvester)
- `status` — TEXT (Saved / Applied / Phone Screen / Interview / Offer / Rejected / Withdrawn)
- `apply_date` — TEXT
- `company` — TEXT
- `job_title` — TEXT
- `match_assessment` — TEXT (owner's manual match note)
- `application_link` — TEXT (where the application was actually submitted)
- `salary_range_top` — TEXT
- `salary_range_source` — TEXT
- `resume_link` — TEXT (link to the specific resume version submitted)
- `contact` — TEXT (recruiter or hiring manager)
- `notes` — TEXT

### `application_responses` — child of applications

One row per custom question response. Replaces the fixed Misc Response A/B/C columns from the spreadsheet.

Fields:
- `id` — PK
- `application_id` — FK to applications
- `sequence` — INTEGER (ordering)
- `question` — TEXT
- `response` — TEXT

### `gmail_events` — owned by Gmail Monitoring project

One row per email processed by the monitor.

Fields:
- `id` — PK
- `gmail_message_id` — TEXT UNIQUE (Gmail's message ID, prevents reprocessing)
- `application_id` — FK to applications (nullable — not all emails will match)
- `company` — TEXT
- `subject` — TEXT
- `received_at` — TEXT
- `characterization` — TEXT (AI's assessment: interview request / rejection / status update / recruiter outreach / other)
- `action_taken` — TEXT (alert sent / label applied / none)
- `processed_at` — TEXT

---

## Cross-Project State Flow

```
jobs (Harvester writes)
  → job_scores (Match Score reads jobs, writes scores)
  → applications (Application Workflow reads jobs, writes applications)
    → application_responses (child)
  → gmail_events (Gmail Monitor reads applications to match companies, writes events)
```

---

## Additional Notes

- All four projects share `team.db` — no separate databases
- Seed data may need to be imported from owner's existing spreadsheets (CSV export). Design for clean import.
- The `jobs` table will also need to integrate with the existing `projects` table in team.db — the job hunting work is project id 2–5
- Include appropriate indexes on frequently queried columns: `job_board+job_id`, `applications.status`, `gmail_events.gmail_message_id`

Please produce the full SQL schema and apply it to `team.db`.
