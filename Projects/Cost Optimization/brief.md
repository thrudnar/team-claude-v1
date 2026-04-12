# Cost Optimization — Project Brief

## Status

**v1 — In Progress**
- Hiring cost optimization manager
- Pricing brief and baseline metrics pending

## Objective

Establish and maintain cost visibility and optimization across all projects that make Anthropic API calls. Ensure every API call pattern is designed with cost awareness, using available discounts (prompt caching, Batch API, model selection) without compromising output quality.

## Versions

### v1 — Baseline & Quick Wins
- **Pricing brief v1** — authoritative reference doc: model rates, cache mechanics (5-min and 1-hour durations), batch rules, stacking math, tool-specific surcharges
- **Baseline cost-per-unit metrics** — "average cost per score" and "average cost per cover letter" calculated from current usage patterns
- **Prompt caching on scorer** — add `cache_control` to `score.py` system prompt. Immediate ROI given sequential batch execution with 0.5s pause (system prompt stays cached entire run)
- No pre-reqs. Can start immediately.

### v2 — Batch & Infrastructure
- **Batch API for scorer** — restructure scoring runs as async batch jobs, triggered after scheduled harvests
- **Shared API utility module** — centralized Anthropic client with caching config, model selection, and usage logging hooks. Replaces independent client construction in `score.py` and `ui/main.py`
- **Prompt caching on cover letters** — triggered by threshold-based cover letter generation (batch all strong matches)
- **Pre-reqs:** Harvester expansion + scheduling (Harvester project), threshold-based cover letter generation (Application Workflow project)

### v3 — Observability
- **Cost logging** — `api_usage` table tracking tokens and cost per API call
- **Cost dashboard** — UI view showing spend by project, cost-per-unit trends, optimization impact
- **Forecasting** — model cost projections when planning volume changes or new API-calling features
- **Pre-reqs:** v2 shared utility (provides the logging hooks), sufficient volume to justify the investment

## Key Metrics

| Metric | Definition | Baseline |
|--------|-----------|----------|
| Cost per score | Total API cost / number of jobs scored in a run | TBD (cost manager's first task) |
| Cost per cover letter | Total API cost / number of cover letters generated | TBD (cost manager's first task) |

## External Resources

- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing) — authoritative price sheet
- `Owner's Inbox/scorer-cost-analysis.md` — existing cost analysis from scorer project

## Team

- **Cost Optimization Manager** (hiring) — project owner
- **Thoth** — implementation partner (shared utility, DB tables)
- **Cicero** — consults on prompt efficiency and token counts
- **Iain** — consults on Anthropic platform best practices

## Cross-Project Dependencies

| This project needs... | From project... |
|----------------------|----------------|
| Harvester scheduling | Job Listing Harvester |
| Threshold-based cover letters | Application Workflow |
| Score prompt token counts | Job Description Match Score |
| Cover letter prompt token counts | Application Workflow |

| Other projects need from us... | |
|-------------------------------|---|
| Caching implementation guidance | Scorer, App Workflow |
| Batch API integration pattern | Scorer |
| Shared API utility | All API-calling projects |
| Cost-per-unit baselines | All API-calling projects |
