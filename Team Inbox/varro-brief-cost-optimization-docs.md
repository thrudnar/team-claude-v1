# Documentation Update Brief — Cost Optimization Project & Stamets Hire

**From:** Adama
**To:** Varro
**Date:** 2026-04-06

---

## What happened

1. **New team member hired:** Stamets — Cost Optimization Manager. Profile at `Team/stamets.md`. Roster already updated by Ocean.
2. **New project chartered:** Cost Optimization — `Projects/Cost Optimization/brief.md`. Active, v1 in progress.
3. **Scorer status has drifted:** The CLAUDE.md pipeline table still says "v1 complete" for Job Description Match Score, but v2 prompt is fully shipped and scored.

---

## Updates needed in CLAUDE.md

### 1. Job Hunting Pipeline table (line ~163)

The Cost Optimization project is **not** part of the Job Hunting Pipeline sequence — it's a cross-cutting concern that spans all API-calling projects. It should get its own section or be added to an appropriate place outside that table.

**Add a new subsection** after the Job Hunting Pipeline section (after the schema files note, before the Guardrails section). Something like:

```markdown
## Cross-Cutting Projects

| Project | Status | Owner(s) |
|---------|--------|----------|
| Cost Optimization | v1 in progress | Stamets |
| Team Photos | Active | Ocean, Cicero, Muybridge |
```

Team Photos has been a project for a while but was never represented in CLAUDE.md either. Good time to fix both.

### 2. Scorer status in pipeline table

Update from:
```
| 2 | Job Description Match Score | v1 complete | ...
```
To:
```
| 2 | Job Description Match Score | v2 complete | ...
```

### 3. Roster hiring pipeline section

`Team/roster.md` line 24 currently says "*(Empty — no open roles at this time)*" — this is correct (pipeline ID 12 is closed). No change needed, just verify.

---

## Files to edit

- `CLAUDE.md` — add cross-cutting projects section, update scorer status
- Verify `Team/roster.md` is current (it should be — Ocean updated it during the hire)

---

## Reference

- `Projects/Cost Optimization/brief.md` — full project brief with v1/v2/v3 roadmap
- `Team/stamets.md` — Stamets's profile
- `Projects/Job Description Match Score/brief.md` — confirms v2 is complete
