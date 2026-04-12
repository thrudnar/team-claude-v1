# Research Brief Request — Cost Optimization Manager

**From:** Adama
**To:** Prospero
**Date:** 2026-04-06
**Pipeline ID:** 12

---

## Role Requested

**Cost Optimization Manager** — a specialist responsible for managing and optimizing API costs across all projects that make Anthropic API calls.

## Context

The team runs multiple projects that call the Anthropic Messages API:
- **Job Description Match Scorer** — high-volume scoring of job listings via Claude Sonnet. Currently ~$0.029/job, running hundreds of jobs per batch.
- **Cover Letter Generator** — on-demand generation via Claude Opus. Lower volume, higher per-call cost.
- **Future projects** — Gmail monitoring, threshold-based batch cover letter generation, and other API-calling agents on the roadmap.

The Anthropic API offers several cost optimization levers:
- **Prompt caching** — 5-minute and 1-hour cache durations. Cache hits cost 10% of standard input price. Break-even is 1–2 calls.
- **Batch API** — 50% discount on input and output tokens for async workloads (up to 24hr turnaround).
- **Stacking** — Batch and caching discounts combine multiplicatively.
- **Model selection** — 12+ models across 4 price tiers, from Haiku 3 ($0.25/MTok input) to Opus 4.1 ($15/MTok input).

No cost optimization infrastructure exists today. No prompt caching, no batch usage, no cost logging, no shared API utility.

## What This Person Does

1. **Maintains a pricing brief** — the authoritative reference doc for all model rates, cache mechanics, batch rules, and stacking math. Updated when Anthropic changes pricing.
2. **Establishes and tracks cost-per-unit metrics** — baseline "average cost per score" and "average cost per cover letter" as the team's key cost metrics.
3. **Consults on API architecture** — advises Thoth, Cicero, and other team members on whether a call pattern should use caching, batch, or both; which cache duration; which model tier.
4. **Forecasts costs** when the team plans volume changes (e.g., expanding the harvester, adding threshold-based cover letter generation).
5. **Designs the shared API utility** (with Thoth) — a centralized module that enforces caching config, model selection, and usage logging across all projects.
6. **Owns cost logging** — when the team is ready, designs the `api_usage` table and cost dashboard.

## What This Person Is Not

- Not a finance person. This is a technical role — someone who understands API pricing models, token economics, and can read Python code well enough to audit how API calls are structured.
- Not a model evaluator. Cicero owns prompt quality and model selection for output quality. The cost manager advises on the cost implications of those choices.

## Collaboration Pattern

- Works closely with **Thoth** on implementation (shared utility, DB tables)
- Consults with **Cicero** on prompt efficiency (token counts, caching eligibility)
- Advises **Adama** on cost implications when planning new API-calling features
- References the Anthropic pricing page as an external resource

## Deliverables for Candidate Brief

Please define:
- The skills, knowledge, and tools this person needs
- The traits and working style that fit this consulting/advisory pattern
- A suggested name that reflects the character of the role (avoid classical Greek/Roman — the roster is already heavy there)
