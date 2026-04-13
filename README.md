# Team Claude v1

A multi-agent AI team I built on the Anthropic Claude API. 12 named agents coordinated by an orchestrator, each carrying a defined role, identity, and model tier assignment within a self-expanding collaborative structure.

---

## What It Is

Most agentic AI work focuses on automating coding tasks. I was interested in a different problem: what organizing principles allow a team of AI agents to collaborate on complex, multi-step knowledge work the way a human team would?

I built a team of specialized agents (research, writing, data harvesting, scoring, quality assurance, image processing, documentation, cost optimization, platform advisory, coordination) sharing a common database and web interface, coordinated by an orchestrator that routes tasks based on agent capabilities.

The practical application was job search automation: harvesting listings, scoring fit, generating application materials, tracking pipeline state. But the real value was learning what works and what breaks when you try to coordinate multiple AI agents on structured, repeatable operations.

---

## The Agent Team

Each agent carries a name drawn from literary, mythological, or historical figures, a defined role, and operating principles specific to their function. The naming started as aesthetic but turned practical: when an orchestrator delegates work, stable identities make coordination natural and outputs attributable.  Note that I only named the first 3 agents, who selected names that had some cultural association to their roles.

| Agent | Role | Model Tier | Responsibilities |
|---|---|---|---|
| **Adama** | Orchestrator | Opus | Receives all tasks, assesses work type, routes to the right team member, enforces hiring process, runs plan review checklist, reports outcomes |
| **Prospero** | Senior Researcher | Sonnet | Defines candidate profiles for new hires, researches skills/tools/traits for roles, provides background context for prompts, writes visual descriptions for team photos |
| **Ocean** | HR Agent | Sonnet | Executes hiring end-to-end, creates team member profiles, updates roster, manages onboarding, coordinates photo pipeline, closes hiring pipeline DB records |
| **Thoth** | Database Specialist | Opus | SQLite schema design, migrations, seed scripts, query optimization, data model integrity, shared API utility implementation |
| **Iris** | Frontend Developer | Opus | FastAPI JSON API, vanilla JS SPA, UI views (roster, projects, tasks, hiring, jobs, scores, applications), static assets |
| **Argus** | Web Harvester | Sonnet | Playwright-based LinkedIn scraping, job listing ingestion, browser session management, description text extraction |
| **Mycroft** | QA & Data Quality | Sonnet | Post-harvest data quality audits, post-scoring calibration audits, pipeline validation, test design, anomaly detection |
| **Cicero** | Prompt Engineer | Opus | LLM prompt design for scoring and cover letters, output calibration, prompt versioning, benchmarking against ground truth |
| **Varro** | Documentation | Sonnet | Maintains CLAUDE.md, schema files, project briefs, ERDs. Triggered after milestones to keep docs current |
| **Muybridge** | Image Processing | Sonnet | Face detection, smart cropping, thumbnail generation via MediaPipe, image pipeline automation |
| **Iain** | Platform Advisor | Opus | Anthropic toolchain audits, model tier fitness reviews, MCP/Agent SDK guidance, memory architecture review |
| **Stamets** | Cost Optimization | Sonnet | API cost tracking, per-token spend analysis, caching strategy, model tier cost justification, spend forecasting |

### How the Team Grew

I seeded the team with three roles: Adama (orchestrator), Prospero (researcher), and Ocean (HR), along with operating procedures for how to expand. When Adama encounters a task that doesn't fit an existing team member, he dispatches Prospero to define a candidate profile, who hands off to Ocean to spawn the new agent and add them to the roster. Every other agent on this list was added through that process as Adama encountered new work.

I defined the initial roles and the expansion process, then gave Adama a variety of tasks that grew the team, expanded the operating procedures, and tuned the orchestrator role. In many regards it was similar to coaching a first-time manager: set the structure, hand over real work, and refine the judgment through iteration rather than specification.

### Model Tier Strategy

I assigned Opus to roles requiring architectural synthesis (Adama, Thoth, Cicero, Iris, Iain), where subtle reasoning errors create expensive downstream rework. Sonnet handles structured, bounded, or procedural work. Iain conducted a model tier fitness review that moved several agents from Opus to Sonnet.

These assignments are forward-looking. In the current single-session Claude Code architecture, every agent runs on whatever model the session uses. The tier assignments become load-bearing when the team moves to a multi-agent architecture with independent invocations, where each agent is spawned with explicit model selection. Getting the assignments right in advance avoids an expensive retrofit when they start hitting the bill.

---

## Architecture

**Orchestrator (Adama)** coordinates multi-step work, routing tasks to specialist agents based on role and capability. Agents report results back through a shared database.

**Shared infrastructure:**
- SQLite database for shared state and work product storage (schema design, migrations, views, FK constraints)
- FastAPI backend serving a vanilla JS SPA for monitoring and reviewing outputs
- CLAUDE.md system prompts and project briefs defining agent behavior
- Playwright for persistent authenticated LinkedIn sessions

**Key patterns:**
- Agent specialization: each agent owns a domain, not a task
- Briefing discipline: agents receive context through structured system prompts, not ad-hoc instructions
- Handoff protocols: outputs from one agent become inputs to the next, with Adama managing the sequence
- Self-expanding team: the hiring pipeline described above is itself an agent-coordinated process, not a manual step

---

## Technology Stack

- **AI**: Anthropic Claude API (Sonnet, Opus — tier-assigned per agent role)
- **Language**: Python
- **Database**: SQLite (schema design, migrations, views, FK constraints)
- **Backend**: FastAPI
- **Frontend**: Vanilla JS SPA, HTML/CSS
- **Scraping**: Playwright (persistent authenticated sessions, LinkedIn)
- **Image Processing**: OpenCV, MediaPipe, Pillow (face detection, smart crop, WebP generation)
- **Built with**: Claude Code

---

## What Worked

- Agent specialization with clear role boundaries made delegation predictable
- The briefing discipline (structured system prompts per agent) produced more consistent outputs than ad-hoc prompting
- A shared database gave agents common ground without requiring direct inter-agent communication
- Named identities made it easier to reason about who should own what
- The model tier strategy created a framework for cost optimization before cost was a real constraint

## What Didn't

The core limitation: v1 mixed operational infrastructure with work products. How agents operated and what they produced were entangled in the same codebase. As the team grew, changes to operations had unintended effects on outputs, and changes to outputs touched operational logic.

This coupling is what drove the reorganization into [Team Claude](https://github.com/thrudnar/team-claude) and eventually the full re-architecture into [TerrAIn](https://github.com/thrudnar/terrain).

---

## Project Status

Complete as a v1 artifact. Superseded by `team-claude` and then `terrain`. Preserved here as a reference for the architectural decisions I made on the first pass, the patterns that held up, and the coupling problem that drove everything that followed.

---

## Relationship to Other Projects

| Project | What it is |
|---|---|
| [Team Claude](https://github.com/thrudnar/team-claude) | Reorganized architecture separating operational infrastructure from work products. The intermediate step. |
| [TerrAIn](https://github.com/thrudnar/terrain) | Production re-architecture. Takes the interface-driven modularity principle further with typed provider adapters, pipeline stages, and a React/FastAPI/MongoDB stack. |
