# Brief for Varro — Deduplication Design Documentation

**From:** Adama
**Date:** 2026-04-03
**Priority:** Normal — document before implementation begins

---

## What happened

The owner spotted apparent duplicate jobs in the DB. Investigation confirmed that Scribd, Inc. posted the same "VP, Data & Analytics" role across 5 cities (Sacramento, San Francisco, Los Angeles, San Diego, Boston) with unique LinkedIn job IDs but byte-for-byte identical descriptions. This prompted a broader design conversation about how deduplication should work as the harvester expands to new job boards.

A design was agreed and added to `Projects/Job Listing Harvester/plan.md` under "Future Work → Deduplication Architecture". Your job is to make sure that design is clearly documented and understandable to anyone picking it up cold.

---

## What to document

### 1. Update `Projects/Job Listing Harvester/plan.md`

The deduplication section has been written — review it for clarity, completeness, and consistency with the rest of the plan. Ensure:
- The three-way classification is easy to scan
- The Scribd example is clearly explained as a canonical reference
- The "anticipated complexity" section signals why implementation is deferred
- The open questions (time threshold X, schema change, cross-board dedup) are clearly flagged as TBD

### 2. Update `Projects/Job Listing Harvester/brief.md`

Add a note that deduplication architecture is a planned feature, deferred pending multi-source expansion. Brief summary only — point to `plan.md` for detail.

### 3. Schema note

The current `jobs` table has `status = 'duplicate'` already modeled. A future `parent_job_id INTEGER REFERENCES jobs(id)` column is anticipated but not yet created. Note this in `schema_job_hunting.sql` as a comment under the `jobs` table definition so it's visible to anyone reading the schema.

---

## Design rationale to preserve

The owner made several specific decisions during the design conversation that should be captured as rationale (the "why"), not just the "what":

- **Why focus only on same company + same title:** Narrows comparison to apples-to-apples, makes AI similarity practical and cheap
- **Why use AI judgement rather than similarity scores:** A rewritten description after a strategic shift is a meaningful signal — you want a judgement call ("same role or different role?"), not a percentage
- **Why defer implementation:** New job board sources (Jobright, BuiltIn, aggregators) are imminent and will introduce cross-board and aggregator-scraping-aggregator scenarios that will add new requirements. Better to implement once the full picture is clear
- **Why isolate dedup logic in its own module:** Needs to be iterable — classification rules will evolve as patterns are observed

---

## Deliverables

1. Reviewed/updated `Projects/Job Listing Harvester/plan.md`
2. Updated `Projects/Job Listing Harvester/brief.md`
3. Comment added to `schema_job_hunting.sql`

Return a summary of changes made to Adama in chat.
