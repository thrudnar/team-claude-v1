# Brief for Iris — Scores page: recency filter

**From:** Adama
**Date:** 2026-04-03

---

## Feature request

Add a recency filter to the Scores view with two options:

1. **Today** — show only jobs where `scored_at` date = today's date
2. **Last run** — show only jobs from the most recent scoring run

---

## Defining "last run"

score.py scores jobs sequentially with ~20s per job and a 0.5s pause between. A full run of 200 jobs takes ~70 minutes. There is no explicit "run ID" in the DB.

Best approach: define "last run" as all scores within **2 hours of the most recent `scored_at` timestamp** for the active score version. This reliably captures a full run without bleeding into previous runs.

SQL to identify last run scores:

```sql
WHERE scored_at >= (
    SELECT datetime(max(scored_at), '-2 hours')
    FROM job_scores
    WHERE score_version = (SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1)
)
```

---

## Implementation notes

- Add the filter as radio buttons or a button group alongside the existing tier checkboxes in the Scores view
- Default state: no recency filter (show all, current behaviour)
- The filter should stack with existing filters (tier checkboxes, etc.) — it narrows the current view, not replaces it
- The filter applies client-side if scores are already loaded, or can be passed as a query param to `/api/scores` — whichever is simpler given the current architecture
- Look at how the existing tier filter is implemented and follow the same pattern

---

## Files

- `ui/static/index.html` — filter UI
- `ui/main.py` — `/api/scores` endpoint if server-side filtering is cleaner

---

## Verification

After implementing:
1. Default view unchanged (all scores visible)
2. "Today" filter shows only scores from today
3. "Last run" filter shows the most recent batch (currently ~150 jobs scored between 00:00–15:30 on 2026-04-03)
4. Combining with tier filter (e.g. Last Run + Tier 1 only) works correctly

No server restart needed if filter is client-side. Required if `/api/scores` is modified.
