# Job Listing Harvester v2 — Plan

**Goal:** Expand harvest coverage beyond the current 3 LinkedIn collections by adding pagination and two new job board sources (Jobright, BuiltIn).

---

## Work Items

### 1. LinkedIn Pagination — COMPLETE (2026-04-02)

**Finding:** LinkedIn collections use a **Next button** (not infinite scroll). Each click
replaces the visible 25 cards with the next 25. `window.scrollTo()` and mouse wheel
events have no effect — the job list container's `scrollTop` stays at 0 regardless.

**Implementation:**
- Button selector: `button.artdeco-button--icon-right`
- Loop: extract IDs → click Next → wait → repeat until cap hit or button absent/disabled
- Cap: `MAX_JOBS_PER_URL = 100` (4 pages × 25 jobs)
- Deduplication: `job_exists()` check before fetching any detail page; `ON CONFLICT` as safety net

**Results:** First paginated run harvested 190 new jobs across 3 collections (183 → 373 total).

**DOM notes** (see `inspect_scroll.py` for full details):
- LinkedIn uses obfuscated CSS class names on the job list container — anchor on
  `data-results-list-top-scroll-sentinel` if the container itself is ever needed
- Two Next buttons exist on the page; `artdeco-button--icon-right` targets the correct one
  (the other is `artdeco-button--circle`, used for job detail navigation)

### 2. Jobright Integration
- Identify Jobright page URLs to harvest (owner to provide)
- Determine auth requirements — does it need a persistent session like LinkedIn?
- Implement scraper following same pattern: list → deduplicate → fetch description
- Map Jobright fields to existing `jobs` schema
- Owner: Argus

### 3. BuiltIn Integration
- Identify BuiltIn page URLs to harvest (owner to provide)
- Determine auth requirements
- Implement scraper following same pattern
- Map BuiltIn fields to existing `jobs` schema
- Owner: Argus

---

## Open Questions

- Which specific Jobright and BuiltIn pages/searches should be harvested? Owner to confirm URLs.
- Does Jobright or BuiltIn require login? If so, `setup_session.py` needs to support multiple profiles.
- Should each new source get its own script or should `harvest.py` be refactored into a multi-source runner?

---

## Dependencies

- `jobs` table schema is stable from v1 — no changes expected for new sources
- `interesting_companies` table (Application Workflow) may eventually feed source URL config, but is not a blocker for v2

---

## Future Work

### Job Posting Date Capture
LinkedIn displays relative posting age on job cards and detail pages (e.g. "1 day ago", "Reposted 6 days ago", "3 weeks ago"). Capture and store this as an inferred absolute date at harvest time.

- Parse the relative time string from the job card or detail page during `get_job_details()`
- Convert to an absolute date by subtracting from harvest date (e.g. "2 days ago" on 2026-04-02 → `posted_date = 2026-03-31`)
- Store in a new `posted_date` column on the `jobs` table (TEXT, ISO 8601)
- Handle edge cases: "Just now", "Reposted N days ago" (use repost date), "Over 30 days ago" (store as approximate)
- Useful for: UI filtering by recency, scoring weight, smarter harvest cap (see below)

### Deduplication Architecture

**Status:** Design agreed, implementation deferred pending multi-source expansion (Jobright, BuiltIn, aggregators).

**Problem:** The same role can appear as multiple distinct job IDs — same company posting across cities, the same listing scraped by aggregator sites, or a role that was closed and relisted months later. Simple `(job_board, job_id)` uniqueness doesn't catch any of these.

**Design — three-way classification:**

When a harvested job matches an existing record on `(company, job_title)`, compare the core role descriptions (requirements, responsibilities — strip boilerplate) and check the time gap:

| Case | Description similarity | Time gap | Action |
|------|------------------------|----------|--------|
| **Duplicate** | High (identical or near-identical) | Short (< X days) | Mark `status = 'duplicate'`, suppress from pipeline |
| **Repost — unchanged** | High | Long (≥ X days) | Keep, flag as repost, link to original, don't re-score |
| **Repost — evolved** | Low (meaningfully different) | Any | Treat as fresh, re-score, flag as repost with link to original |

**Key design decisions:**
- **Scope:** Compare only within same `company` + `job_title` — this constrains the comparison to apples-to-apples and makes AI-assisted similarity practical
- **Description focus:** Strip company culture/benefits boilerplate; compare only the role-specific sections (responsibilities, requirements, qualifications)
- **Similarity method:** Use Claude (Haiku, cheap and fast) to assess whether the substantive role requirements have changed — return a judgement (`same` / `repost_unchanged` / `repost_evolved`), not a raw similarity score
- **Time threshold X:** TBD — likely 30–60 days; to be confirmed once more repost data is observed
- **Schema:** `jobs` table already has `status = 'duplicate'`. Lineage tracking (linking a repost to its original) will require a new column, e.g. `parent_job_id INTEGER REFERENCES jobs(id)`
- **Placement:** Dedup logic runs inside Argus at harvest time, as a check triggered when `(company, job_title)` collision is detected — not as a post-processing pass
- **Iterability:** Dedup logic should be isolated in its own module/function so the classification rules can be updated independently of the harvest loop

**Known example:** Scribd, Inc. "VP, Data & Analytics" — 5 identical postings across Sacramento, San Francisco, Los Angeles, San Diego, and Boston, all harvested within 3 days. Byte-for-byte identical descriptions. Classic multi-city repost.

**UI / downstream table handling:**
- The Scores view (`/api/scores`) filters on `archived = 0` but does NOT filter on `status != 'duplicate'` — duplicates remain visible in the Scores inbox unless archived
- When marking jobs as `status = 'duplicate'`, also set `archived = 1` to hide them from all views
- `job_scores` rows on duplicates are harmless to leave in place — the descriptions are identical so scores are identical; archiving the job is sufficient
- The `applications` table should be checked before marking any job duplicate — if an application row exists, preserve that job as the keeper regardless of other priority rules

**Keeper selection priority** (when multiple listings exist for same company + title):
1. Has an `applications` row with `status = 'applied'`
2. Has any `applications` row (saved/interested)
3. Already scored
4. Location scoring (descending): remote > "United States" > not stated/blank > hybrid in SF/Denver > onsite in SF/Denver > any other named location
5. Lowest job ID (earliest harvested)

**Exec recruiting firms:**
- Recruiting/staffing firms (e.g. Elios Talent, RemoteHunter) post the same underlying role across multiple cities or repost frequently — they are not the actual employer
- Dedup logic should treat the `company` field as the recruiter, not the hiring company, which means same-title reposts by the same recruiter are duplicates even if the underlying employer differs
- Future enhancement: where possible, extract the actual hiring company from the description text and use that as an additional dedup signal
- Description formatting variations (extra blank lines, USD vs CAD salary rendering) are not substantive differences — similarity check should normalize whitespace before comparing

**Anticipated complexity from multi-source expansion:**
- Same role published on LinkedIn, Jobright, and BuiltIn simultaneously → cross-board dedup needed (currently `UNIQUE` constraint is per `job_board`)
- Aggregator sites scraping each other → description text may be subtly mutated even for the same underlying listing
- These cases will inform the final implementation once new sources are live

### Smarter Harvest Cap
Replace the current blunt `MAX_JOBS_PER_URL = 100` with a smarter stopping rule:

> "Keep paginating until we've added 100 jobs to the DB that are both (a) not already in the DB and (b) posted within the last 3 weeks."

- Stop paginating early if a page is full of old or already-seen jobs — no point fetching detail pages for stale listings
- Naturally manages volume without pulling irrelevant listings from deep pages
- The new-job count (100) and age cutoff (3 weeks) should be named constants, easy to tune
- **Depends on posting date capture being implemented first**
