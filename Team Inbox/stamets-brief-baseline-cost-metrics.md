# Task Brief — Baseline Cost-Per-Unit Metrics & Cost Data Architecture

**From:** Adama
**To:** Stamets
**Date:** 2026-04-06
**Project:** Cost Optimization v1

---

## Context

This is your first assignment on the team. It has two parts: (1) establish today's cost-per-unit baselines, and (2) design where cost data lives so it can grow with the team over time.

These baselines are not a one-off report. They're the first entries in what will become an ongoing cost record — a living dataset that we'll use to track the impact of optimizations, associate cost changes with prompt version releases, model the cost implications of new features before we build them, and eventually feed a cost dashboard (v3 roadmap).

Think of this as laying the foundation for the team's cost observability layer. Start simple, but design for the trajectory.

---

## Part 1 — Baseline Cost-Per-Unit Metrics

Calculate two numbers:

### 1. Average cost per score (current)

Prior analysis exists: `Owner's Inbox/scorer-cost-analysis.md` (prepared 2026-04-02).

Key facts from that analysis:
- Model: `claude-sonnet-4-6` ($3.00/MTok input, $15.00/MTok output)
- v2 prompt: ~7,455 input tokens, ~428 output tokens per job
- Estimated cost: ~$0.029/job

**Your job:** Validate this number. Confirm or refine the token estimates. Record it as the official v2 baseline with your methodology visible.

### 2. Average cost per cover letter (current)

No prior analysis exists. You'll need to determine:
- Which model is configured in `cover_letter_prompts` table (query `team.db`)
- The system prompt and user prompt template token counts
- Typical output length (check existing cover letters in `applications` table, or estimate from `max_tokens` in the generation code at `ui/main.py` around line 293)
- Calculate cost per generation

**Source files:**
- `ui/main.py` — `generate_cover_letter()` function (~line 270)
- `team.db` — `cover_letter_prompts` table (query for model, system_prompt, user_prompt_template)
- `team.db` — `applications` table (cover_letter column for output length samples)

---

## Part 2 — Cost Data Storage Design

We need a place to store cost metrics that can grow over time. The trajectory looks like this:

**Now (v1):** Two baseline numbers — cost per score, cost per cover letter. Recorded once, manually calculated.

**Soon (v1+):** Baselines per prompt version. When Cicero ships scorer v3 or cover letter prompt v2, we record new cost-per-unit baselines and can compare against previous versions.

**Later (v2):** When the shared API utility is built, every API call will log actual token usage. Cost-per-unit becomes a computed aggregate, not a manual estimate.

**Eventually (v3):** A cost dashboard, trend lines, forecasting, cost-per-unit over time, cost impact of prompt version changes.

### Design question for you

The owner suggests **starting with a CSV** and graduating to a **DB table when we outgrow it**. This makes sense — a CSV is human-readable, easy to inspect, trivial to start, and adequate for manually-recorded baselines. A DB table becomes necessary when we have per-call logging (v2+) and need aggregation queries.

Propose a storage plan:
- **CSV for v1:** What columns? Where does it live? (`Projects/Cost Optimization/` is the natural home.) What's a row — one baseline measurement? One prompt version? Think about what you'll want to `diff` or chart later.
- **DB migration trigger:** What condition tells us it's time to move from CSV to a DB table? (Likely: when the shared API utility starts logging per-call data and manual CSV updates can't keep up.)
- **Schema sketch:** Even though we won't build the DB table yet, sketch what `cost_baselines` or `api_usage` might look like so Thoth has a head start when the time comes.

---

## Deliverables

1. **Baseline report** — delivered to `Owner's Inbox/cost-baselines-v1.md`. Two cost-per-unit numbers with full methodology (token counts, model pricing, assumptions).
2. **CSV design** — the empty CSV with headers, plus a brief note on the schema rationale. Delivered to `Projects/Cost Optimization/cost_baselines.csv` (or whatever name you choose).
3. **Storage roadmap** — a short section in the baseline report covering: CSV now, DB later, migration trigger, schema sketch.

---

## Resources

- **Anthropic pricing:** https://platform.claude.com/docs/en/about-claude/pricing
- **Existing scorer cost analysis:** `Owner's Inbox/scorer-cost-analysis.md`
- **Scorer code:** `Projects/Job Description Match Score/scorer/score.py`
- **Cover letter code:** `ui/main.py` (search for `generate_cover_letter`)
- **Database:** `team.db` (SQLite) — tables: `cover_letter_prompts`, `applications`, `score_prompts`, `job_scores`
- **Project brief:** `Projects/Cost Optimization/brief.md`

---

## Collaboration

- **Thoth** — if you need help with DB queries or want to discuss the future schema sketch, pull him in
- **Cicero** — can provide exact token counts for prompts if the character-estimate method isn't precise enough
- **Iain** — can advise on whether the Anthropic SDK exposes actual token usage in response objects (it does — `response.usage.input_tokens` and `response.usage.output_tokens`)

---

## One more thing

This is the start of something that will matter more over time, not less. As we add more API-calling projects, expand harvesting volume, introduce threshold-based batch cover letters, and eventually build always-on agents — the cost data you establish now becomes the team's institutional memory for spend. Design it like you'll be reading it in six months and comparing it against numbers that don't exist yet.
