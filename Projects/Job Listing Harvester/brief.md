# Job Listing Harvester — Project Brief

## Status

**v1 — Complete (2026-04-01)**
- Harvests 3 LinkedIn collections: `top-applicant`, `recommended`, `remote-jobs`
- Returns ~25 jobs per collection (LinkedIn's page size)
- All fields populated: title, company, location, work_type, description_text, source_collection
- 72 jobs currently in DB
- Run: `cd harvester && source .venv/bin/activate && python harvest.py`
- First-time setup: `python setup_session.py` (one-time LinkedIn login, saves persistent browser profile to `browser-profile/`)

**v1.1 — Queued (Argus)**
- Pagination: LinkedIn shows 25 jobs/page with a "next page" button; currently only page 1 is harvested

**v2+ — Planned**
- Additional sources: BuiltIn, Jobright
- LinkedIn email digest parsing
- LinkedIn emails (direct job notifications)
- LinkedIn job alerts emails
- Generic company careers pages

---

## Objective

Scrape job listings from LinkedIn and other sources into the `jobs` table in `team.db`. One row per job, unique on `(job_board, job_id)`. Store the full job description text at harvest time so downstream projects (Match Score) never need to re-fetch pages.

## Scope

- Phase 1: LinkedIn web scraping via Playwright with persistent authenticated session
- Phase 2: LinkedIn email parsing
- Phase 3: BuiltIn, Jobright
- Future: company career pages

## Source URLs

### LinkedIn Collections (require authenticated session)

| Collection | URL |
|---|---|
| Top Applicant | https://www.linkedin.com/jobs/collections/top-applicant/ |
| Recommended | https://www.linkedin.com/jobs/collections/recommended/ |
| Remote Jobs | https://www.linkedin.com/jobs/collections/remote-jobs/ |

These are personalized pages — content is specific to the owner's LinkedIn profile. New listings appear as LinkedIn updates its recommendations.

## Technical Approach

- **Browser:** Playwright with bundled Chromium, persistent profile stored in `Projects/Job Listing Harvester/browser-profile/`
- **Session:** Owner logs in once via setup script; session reused on all subsequent runs
- **Deduplication:** `(job_board, job_id)` unique constraint in DB handles this automatically
- **Description storage:** Full page content stored in `jobs.description_text` at harvest time — do not fetch live at scoring time
- **Scheduling:** Manual trigger initially; cron job once reliable

## Harvest Workflow

1. Load each collection URL using saved session
2. Scroll/paginate to load all job cards
3. For each job card: extract job ID, title, company, location, work_type, job_url
4. Check DB — skip `(job_board, job_id)` pairs already stored
5. For each new job: fetch individual job page, extract full description_text
6. Write row to `jobs` table with `is_new = 1`, `status = 'new'`
7. Update `most_recent_date_seen` for any jobs seen again that already exist

## Output

Rows in `jobs` table. Fields: `job_board`, `job_id`, `company`, `job_title`, `location`, `work_type`, `job_url`, `description_text`, `first_date_seen`, `most_recent_date_seen`, `is_new`, `status`.

## Constraints

- Be polite: rate limit requests, add delays between page loads
- Do not hammer LinkedIn — this is a personal tool, not a mass scraper
- LinkedIn may update page structure; the scraper should fail gracefully and report clearly when selectors break

## Team
<!-- Populated by Adama as team members are assigned -->
- **Argus** — Web Harvester (hiring in progress)

## Background

See `context/portfolio-overview.md` for the full job hunting portfolio context.
