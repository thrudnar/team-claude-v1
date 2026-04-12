-- Job Hunting Portfolio Schema
-- Maintained by Thoth
-- Last updated: 2026-04-07
-- Applies to: team.db (alongside existing team management tables)
--
-- IMPORTANT: This file is the authoritative schema reference.
-- When columns are added via ALTER TABLE, update this file immediately.
-- Do not let this file fall behind the live DB.

-- ============================================================
-- PROJECT 1: HARVESTER
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    job_board             TEXT    NOT NULL,
    job_id                TEXT    NOT NULL,
    company               TEXT,
    job_title             TEXT,
    location              TEXT,
    work_type             TEXT    CHECK (work_type IN ('remote', 'hybrid', 'onsite', 'unknown')),
    job_url               TEXT,
    description_text      TEXT,   -- full page content, stored at harvest time
    source_collection     TEXT,   -- e.g. 'top-applicant', 'recommended', 'remote-jobs'
    first_date_seen       TEXT    NOT NULL DEFAULT (date('now')),
    most_recent_date_seen TEXT    NOT NULL DEFAULT (date('now')),
    source_email_id       TEXT,   -- nullable: for future email-sourced listings
    is_new                INTEGER NOT NULL DEFAULT 1,
    status                TEXT    NOT NULL DEFAULT 'new'
                                  CHECK (status IN ('new', 'scored', 'skip', 'duplicate')),
    apply_flag            INTEGER NOT NULL DEFAULT 0,  -- manually set by owner in UI
    archived              INTEGER NOT NULL DEFAULT 0,  -- soft-delete; omitted from all views
    created_at            TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (job_board, job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_board_id   ON jobs (job_board, job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_company    ON jobs (company);

-- ============================================================
-- PROJECT 2: MATCH SCORE
-- ============================================================

CREATE TABLE IF NOT EXISTS score_prompts (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    version                TEXT    NOT NULL UNIQUE,   -- e.g. 'v1', 'v2'
    model                  TEXT    NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
    system_prompt          TEXT    NOT NULL,
    user_prompt_template   TEXT    NOT NULL,          -- use {description_text} placeholder
    cover_letter_threshold INTEGER NOT NULL DEFAULT 75,
    notes                  TEXT,                      -- design rationale, what changed vs prior version
    created_at             TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_scores (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id                INTEGER NOT NULL REFERENCES jobs (id),
    score_version         TEXT    NOT NULL DEFAULT 'v1',
    overall_score         INTEGER CHECK (overall_score BETWEEN 0 AND 100),
    skills_score          INTEGER CHECK (skills_score BETWEEN 0 AND 100),
    seniority_score       INTEGER CHECK (seniority_score BETWEEN 0 AND 100),
    work_type_score       INTEGER CHECK (work_type_score BETWEEN 0 AND 100),
    work_arrangement      TEXT,   -- extracted fact: Remote | Hybrid | On-site | Not stated
    salary_range          TEXT,   -- extracted fact: stated range as string, stated range as string
    match_summary         TEXT,   -- prose assessment (v1.1 will restructure into 3 labeled sections)
    strengths             TEXT,   -- pipe-delimited: 'strength one | strength two | strength three'
    gaps                  TEXT,   -- pipe-delimited: 'gap one | gap two | gap three'
    recommendation        TEXT,   -- STRONG FIT | GOOD FIT | MARGINAL FIT | SKIP
    reasoning             TEXT,   -- model's chain-of-thought or scoring rationale
    cover_letter          TEXT,   -- generated for high-match jobs (not yet in use)
    resume_customizations TEXT,   -- tailoring recommendations (not yet in use)
    scored_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (job_id, score_version)  -- one score per job per version
);

CREATE INDEX IF NOT EXISTS idx_job_scores_job_id  ON job_scores (job_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_overall ON job_scores (overall_score);

CREATE TABLE IF NOT EXISTS score_tests (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id            INTEGER NOT NULL REFERENCES jobs(id),
    prompt_version    TEXT    NOT NULL,
    model             TEXT    NOT NULL,
    overall_score     INTEGER CHECK (overall_score BETWEEN 0 AND 100),
    skills_score      INTEGER CHECK (skills_score BETWEEN 0 AND 100),
    seniority_score   INTEGER CHECK (seniority_score BETWEEN 0 AND 100),
    work_type_score   INTEGER CHECK (work_type_score BETWEEN 0 AND 100),
    work_arrangement  TEXT,
    salary_range      TEXT,
    match_summary     TEXT,
    strengths         TEXT,
    gaps              TEXT,
    recommendation    TEXT,
    reasoning         TEXT,
    scored_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (job_id, prompt_version)
);

CREATE INDEX IF NOT EXISTS idx_score_tests_job_id ON score_tests (job_id);
CREATE INDEX IF NOT EXISTS idx_score_tests_version ON score_tests (prompt_version);

-- ============================================================
-- PROJECT 3: APPLICATION WORKFLOW
-- ============================================================

CREATE TABLE IF NOT EXISTS applications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id              INTEGER REFERENCES jobs (id),  -- nullable: may predate harvester
    status              TEXT    NOT NULL DEFAULT 'new'
                                CHECK (status IN (
                                    'new', 'applied', 'waiting', 'phone_screen',
                                    'interview', 'offer', 'rejected', 'withdrawn', 'dead'
                                )),
    apply_date          TEXT,
    company             TEXT,
    job_title           TEXT,
    match_assessment    TEXT,   -- owner's manual match note
    application_link    TEXT,   -- where the application was submitted
    salary_range_top    TEXT,
    salary_range_source TEXT,
    resume_link         TEXT,   -- link to the specific resume version submitted
    contact             TEXT,   -- recruiter or hiring manager
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    job_board           TEXT,
    board_job_id        TEXT,   -- job identifier on the source board
    cover_letter        TEXT,   -- generated cover letter text
    source              TEXT    CHECK (source IN ('harvested', 'imported'))
                                -- 'harvested': row created via star→apply from jobs table
                                -- 'imported':  row imported from pre-pipeline spreadsheet
);

CREATE INDEX IF NOT EXISTS idx_applications_status  ON applications (status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id  ON applications (job_id);
CREATE INDEX IF NOT EXISTS idx_applications_company ON applications (company);

-- DEFERRED: application_responses is unpopulated and excluded from v2 scope.
-- Retained in schema for future use. Do not build against this table until activated.
CREATE TABLE IF NOT EXISTS application_responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id  INTEGER NOT NULL REFERENCES applications (id),
    sequence        INTEGER NOT NULL DEFAULT 1,
    question        TEXT,
    response        TEXT
);

CREATE INDEX IF NOT EXISTS idx_app_responses_app_id ON application_responses (application_id);

-- ============================================================
-- PROJECT 3 (cont.): COVER LETTER PROMPTS
-- ============================================================

CREATE TABLE IF NOT EXISTS cover_letter_prompts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    version              TEXT    NOT NULL UNIQUE,   -- e.g. 'v1', 'v2'
    model                TEXT    NOT NULL DEFAULT 'claude-sonnet-4-6',
    system_prompt        TEXT    NOT NULL,
    user_prompt_template TEXT    NOT NULL,
    notes                TEXT,                      -- design rationale, what changed vs prior version
    created_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- PROJECT 4: GMAIL MONITORING
-- ============================================================

CREATE TABLE IF NOT EXISTS gmail_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    gmail_message_id    TEXT    NOT NULL UNIQUE,  -- prevents reprocessing
    application_id      INTEGER REFERENCES applications (id),  -- nullable
    company             TEXT,
    subject             TEXT,
    received_at         TEXT,
    characterization    TEXT    CHECK (characterization IN (
                                    'interview_request', 'rejection', 'status_update',
                                    'recruiter_outreach', 'offer', 'other'
                                )),
    action_taken        TEXT    CHECK (action_taken IN (
                                    'alert_sent', 'label_applied',
                                    'alert_and_label', 'none'
                                )),
    processed_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_gmail_events_message_id  ON gmail_events (gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_gmail_events_application ON gmail_events (application_id);
CREATE INDEX IF NOT EXISTS idx_gmail_events_company     ON gmail_events (company);

-- ============================================================
-- INTERESTING COMPANIES (feeds Project 1 v2 harvester + future scoring)
-- Owner-managed table. Not FK'd to applications — joined by company name
-- for read-only lookups. This is intentional, not a schema gap.
-- ============================================================

CREATE TABLE IF NOT EXISTS interesting_companies (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    list_source          TEXT,
    name                 TEXT    NOT NULL,
    description          TEXT,
    my_interest_drivers  TEXT,
    my_apprehensions     TEXT,
    my_interest_level    TEXT,
    size                 TEXT,
    round                TEXT,
    sector               TEXT,
    culture              TEXT,
    purpose_impact       TEXT,
    evilness             TEXT,
    tech_centric         TEXT,
    up_or_out            TEXT,
    why                  TEXT,
    who_i_know           TEXT,
    careers_url          TEXT,
    created_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_interesting_companies_name ON interesting_companies (name);
