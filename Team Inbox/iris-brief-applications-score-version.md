# Brief for Iris — Fix score version in Applications view

**From:** Adama
**Date:** 2026-04-03

---

## Bug

The Applications view (`/api/applications`) shows a blank `overall_score` for any job that was only scored under v2 (and has no v1 score). The query hardcodes `score_version = 'v1'`.

## File

`ui/main.py`, `GET /api/applications` endpoint (~line 210)

## Current query (broken)

```sql
LEFT JOIN job_scores s
       ON j.id = s.job_id
      AND s.score_version = 'v1'
```

## Fix

Use the latest available score version, consistent with how `/api/scores` does it:

```sql
LEFT JOIN job_scores s
       ON j.id = s.job_id
      AND s.score_version = (
          SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1
      )
```

## Verification

After fixing, query `/api/applications` and confirm `overall_score` is populated for jobs that have only v2 scores. The 7 most recently starred jobs should now show scores in the 75–88 range.

No server restart needed — this is a Python/API change so a restart is required.
