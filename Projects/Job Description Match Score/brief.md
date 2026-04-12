# Job Description Match Score — Project Brief

## Status

**v1 — Complete (2026-04-01)**
- 72 jobs scored against prompt v1
- Scores visible in UI at `#scores` with filter tabs, assessment modal, apply flag toggle
- Prompt versioned in DB (`score_prompts` table, version `v1`)

**v1.1 — Queued (Cicero)**
- Restructure `match_summary` into three sections: "Where you're strong" / "Where the gap is real" / "My honest take" — matching the format of the sample assessments in `context/`
- Fix recommendation/score calibration drift (score and label occasionally disagree)

**v2 — Planned (Cicero + Thoth + Iris)**
- Feedback loop: capture owner's reason for not starring a high-scoring job
- New DB structure for feedback, modal input in UI, feeds into future prompt calibration

---

## Objective

For each job listing in the `jobs` table, evaluate the fit between the job description and the owner's background and preferences. Store structured scores and commentary in the `job_scores` table. State is managed via `(job_id, score_version)` — each job is scored once per prompt version. Rescoring with a new version is a deliberate action.

---

## Scope

- **Input:** `jobs.description_text` — full job page content stored at harvest time
- **Output:** Rows in `job_scores` — scores, commentary, work arrangement, salary range, recommendation tier
- **Model:** Claude Haiku (scoring); Claude Sonnet reserved for future cover letter generation
- **Prompt ownership:** Cicero. All prompt versions live in `score_prompts` table — never in loose files.
- **Cover letters:** Schema supports them (`cover_letter` column); generation not yet triggered. Manual review gate comes first.

---

## Score Dimensions

All scores are integers 0–100.

| Field | What it measures |
|-------|-----------------|
| `overall_score` | Holistic fit — weighted combination of skills, seniority, work arrangement |
| `skills_score` | Match between the candidate's technical/domain skills and role requirements |
| `seniority_score` | Match between role scope/title and the candidate's target seniority level |
| `work_type_score` | Contextual work arrangement fit — weighs arrangement + location + comp together |

**Text fields:** `match_summary`, `strengths` (pipe-delimited), `gaps` (pipe-delimited), `recommendation` (STRONG FIT / GOOD FIT / MARGINAL FIT / SKIP)

**Extracted facts:** `work_arrangement` (Remote/Hybrid/On-site/Not stated), `salary_range` (stated range as string)

---

## Recommendation Thresholds

| Label | Score Range |
|-------|------------|
| STRONG FIT | ≥ 75 |
| GOOD FIT | 60–74 |
| MARGINAL FIT | 45–59 |
| SKIP | < 45 or hard disqualifier present |

**Hard disqualifiers:** stated base salary explicitly below target.

**Work arrangement:** Not a hard disqualifier. Remote preferred; hybrid/on-site acceptable for strong comp in SF Bay Area or Denver metro. Cicero's prompt applies contextual judgment.

---

## How to Run the Scorer

```bash
cd "Projects/Job Description Match Score/scorer"
export ANTHROPIC_API_KEY="..."

# Score all unscored jobs (v1 prompt)
.venv/bin/python3 score.py

# Options
.venv/bin/python3 score.py --dry-run       # print results, don't write
.venv/bin/python3 score.py --limit 5       # score only 5 jobs
.venv/bin/python3 score.py --version v1    # specify prompt version (default: v1)
```

To update the prompt in place: `python seed_prompt_v1.py --update`
To add a new version: create `seed_prompt_v2.py` following the same pattern.

---

## Team

- **Cicero** — Prompt Engineer. Owns `score_prompts`. Designs, versions, and benchmarks all scoring prompts.
- **Prospero** — Senior Researcher. Built the scorer script (`score.py`). Consults on owner profile framing.
- **Iris** — Frontend Developer. Built the Scores UI view, assessment modal, apply flag toggle.
- **Thoth** — Database Specialist. Owns `job_scores` and `score_prompts` schema.
- **Mycroft** — QA. Post-scoring data quality audits.

---

## Background

See `context/` for supporting materials:
- `Owner — Job Hunt Project System Prompt.txt` — authoritative owner profile used in prompt design
- `Owner — Job Hunt Project Memory.txt` — job search context, preferences, history
- `example match assessement 1–4.txt` — human-reviewed ground truth assessments used to calibrate v1
- `match prompt prototype.txt` — original prototype prompt (superseded by v1)
- `portfolio-overview.md` — full job hunting portfolio context
