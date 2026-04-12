# Application Workflow — Project Brief

## Objective

Build and maintain a record-keeping system for tracking job applications from submission through to outcome. Includes import of historical applications, a UI view with filters, and automated application creation when a job is starred in the Scores view.

## Scope

- `applications` table with status pipeline: new → applied → waiting → phone_screen → interview → offer → rejected / withdrawn / dead
- `application_responses` table for Q&A (deferred past v2, annotated in schema)
- Spreadsheet import of historical data
- `interesting_companies` table (owner-managed, standalone, not FK'd to applications — joined by company name for read-only display)
- Web UI: Applications view with status/company filters, interesting company indicators
- Star → application wiring in Scores view
- Cover letter generation via voice-of-tim skill (skills beta API)

## Background

See `context/` for supporting materials.

## Status

v2 complete (2026-04-07)

## v2 Changes

- **Status pipeline:** Removed `saved` status. `new` is the sole initial state. Default filter falls back to `all` when no `new` records exist.
- **Schema integrity:** Fixed 3 broken FK references in imported records. Set `source='harvested'` on 13 records with null source. Apply endpoint now sets `source='harvested'` on new records.
- **Dynamic version selection:** Apply endpoint and cover letter generation both use latest score/prompt version, not hardcoded `v1`.
- **Cover letter prompt v2:** System prompt retains factual bio, drops VOICE AND STYLE section. User prompt drops rigid 3-paragraph template, adds anti-formula instruction. Voice authority delegated to voice-of-tim skill via Anthropic skills beta API.
- **Interesting companies:** Applications view shows a star indicator next to companies that appear in `interesting_companies`.
- **UI fixes:** Status labels updated (added `new`, `rejected`; removed `saved`). Status dropdown matches schema. Tab highlighting corrected.

## How to Run / Key Behaviors

- Starring a job in the Scores view creates an application row (status: `new`), populates available fields from `jobs` and `job_scores`, and triggers async cover letter generation via the Claude API with voice-of-tim skill
- Cover letter prompt is stored in the `cover_letter_prompts` table; generation uses the latest version automatically
- If the skills beta API is unavailable, cover letter generation falls back to standard API call
- Applications UI: filter tabs by status (defaults to `new`, falls back to `all`), inline status dropdown, editable notes field, cover letter modal, job title links to the external posting, star icon on interesting companies

## Constraints & Notes

- `applications.job_id` is nullable — applications may predate the harvester
- `interesting_companies` is owner-managed and standalone; joined by company name (case-insensitive), not FK'd
- `application_responses` is deferred — table exists but is unpopulated and excluded from v2 scope
- Cover letter generation depends on skills beta (`skills-2025-10-02`) — monitor for API changes

## Team

| Member | Role |
|--------|------|
| Thoth  | Schema design, DB imports, generation code |
| Iris   | UI and API |
| Cicero | Cover letter prompt design |
| Varro  | Documentation |
