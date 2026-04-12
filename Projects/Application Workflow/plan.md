# Application Workflow v2 — Plan

**Goal:** Reconcile states, schemas, and data integrity across the major entities that make up the application workflow. v1 shipped the core pipeline; v2 makes it trustworthy and consistent.

---

## Work Items

### 1. Status Pipeline Audit
The `applications` status pipeline (`saved → applied → waiting → phone_screen → interview → offer → rejected / withdrawn / dead`) was designed upfront. Validate it against real usage.

- Review any applications already in the DB — do their statuses reflect reality?
- Identify any missing or ambiguous transition states
- Confirm terminal states are correct and complete
- Owner: Thoth

### 2. Schema Integrity Review
Several design decisions in v1 carry intentional flexibility (nullable FKs, standalone tables). Audit whether they're creating data quality gaps.

- `applications.job_id` is nullable — are null-job-id rows handled correctly everywhere they're read?
- `interesting_companies` is not FK'd to `applications` — confirm this is still the right call; document it explicitly
- `application_responses` exists but is unpopulated — decide: keep, populate, or defer?
- Cross-check `applications` fields populated at star-time against what `jobs` and `job_scores` actually provide
- Owner: Thoth

### 3. Cover Letter Pipeline Integrity
Cover letter generation is async and fires at star-time. Confirm the pipeline is reliable.

- Are there applications with missing cover letters that should have one?
- Is the `cover_letter_prompts` v1 prompt producing good output? Flag for owner review if not.
- Owner: Thoth (schema), Iris (UI display)

### 4. UI State Consistency
The Applications view filters and displays state from the DB. Validate it reflects the schema correctly.

- Default filter (`new`) — confirm it matches the status value written at star-time
- Status dropdown — confirm all valid statuses are present and in logical order
- Edge cases: applications with null job_id, applications with no cover letter
- Owner: Iris

### 5. Cover Letter Prompt v2

**Status:** Design phase. Experiment completed 2026-04-03; results inform the architecture below.

**Context:** The v1 cover letter prompt (stored in `cover_letter_prompts`) has two parts: a system prompt containing the owner's full bio, career proof points, and a VOICE AND STYLE section, and a user prompt template with rigid 3-paragraph structure instructions. An A/B experiment tested the impact of adding a 4-page writing style guide alongside the existing prompt. The style guide version produced noticeably more authentic output: better tempo, tone, and language that the owner connected with as a genuine representation of his point of view.

**Architecture — style guide as external universal resource:**

The style guide is not owned by this project. It is a universal resource that the owner maintains independently for use across claude.ai chat, Claude Code, API calls, and Cowork. The team's cover letter pipeline is a *consumer* of this resource, not its author.

Implementation:
- The cover letter generation code (`ui/main.py`, `generate_cover_letter()`) reads the style guide at call time from a known file path or DB location (TBD by owner once the universal resource architecture is established)
- The style guide is injected into the user prompt just before the generation instruction, keeping it fresh in context
- The system prompt retains the owner's bio and career proof points (factual reference material), while voice/style authority shifts to the external style guide
- If the style guide is unavailable at call time, the pipeline falls back to the existing VOICE AND STYLE section in the system prompt — no hard dependency

**Work items for v2 prompt:**

1. **Cicero** writes the v2 prompt, incorporating the style guide integration point and revising the system prompt structure
2. **Thoth** adds v2 row to `cover_letter_prompts` table, updates the generation code to read and inject the external style guide
3. **Iris** wires the v1→v2 version reference (same fix as the scores version issue: use latest version, not hardcoded)

**External coaching advice — areas to explore (not yet validated, treat as hypotheses to test):**

These observations came from prompt engineering analysis. They are directional, not prescriptive. Each should be tested in isolation before adopting.

- **Remove paragraph structure instructions** — the rigid 3-paragraph template in the user prompt is the most likely source of residual stiffness in the output. Primary hypothesis to test first.
- **Instruction density** — the system prompt is long and detailed. There may be a diminishing-returns threshold where more rules produce more robotic output because the model executes a checklist rather than writes prose. Worth testing a leaner version.
- **Example quality over rule quantity** — swap some prescriptive rules for additional approved cover letter examples. Models often internalize voice better from examples than from descriptions of voice.
- **Instruction ordering** — examples placed at the end of a long prompt sometimes receive less weight. Try moving few-shot examples earlier in the prompt.
- **Explicit anti-formula instruction** — a single line like "Do not produce a formulaic structure. Write the letter as a coherent piece of prose, not as three separate answers to three separate prompts" can be surprisingly effective at breaking template-following behavior.

**Testing approach:** follow the same A/B methodology used in the style guide experiment — fully populated prompts tested in incognito chat against the Arcadia job as the baseline case, one variable changed per test.

---

## Open Questions

- Should `application_responses` be populated in v2, or deferred to a later version?
- Is there a defined owner for the `interesting_companies` table in this project, or is it managed externally?

---

## Dependencies

- v1 data already in DB — changes must be non-destructive and backward-compatible
- Harvester v2 adds new job sources; confirm `applications` correctly handles jobs from any `job_board` value
