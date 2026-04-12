-- Team Claude — SQLite Schema
-- Maintained by Thoth
-- Created: 2026-03-31

-- ============================================================
-- TEAM
-- ============================================================

CREATE TABLE IF NOT EXISTS team_members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL,
    domain      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    date_joined TEXT NOT NULL DEFAULT (date('now'))
);

-- ============================================================
-- PROJECTS
-- ============================================================

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'on_hold', 'completed', 'cancelled')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- TASKS
-- ============================================================

CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id),   -- nullable: not all tasks belong to a project
    title           TEXT NOT NULL,
    description     TEXT,
    assigned_to     INTEGER REFERENCES team_members(id),
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority        TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- HIRING PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS hiring_pipeline (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    role_requested      TEXT NOT NULL,
    brief_file          TEXT,   -- path to Prospero's candidate brief in Team Inbox
    status              TEXT NOT NULL DEFAULT 'researching' CHECK (status IN ('researching', 'hiring', 'completed', 'cancelled')),
    hired_member_id     INTEGER REFERENCES team_members(id),
    requested_at        TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at        TEXT
);

-- ============================================================
-- WORK LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS work_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER REFERENCES tasks(id),
    team_member_id  INTEGER REFERENCES team_members(id),
    action          TEXT NOT NULL,
    notes           TEXT,
    logged_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- SEED: founding team members
-- ============================================================

INSERT INTO team_members (name, role, domain, date_joined) VALUES
    ('Prospero', 'Senior Researcher',   'Skills research & candidate profiling', '2026-03-31'),
    ('Ocean',    'HR Agent',            'Talent acquisition & team building',     '2026-03-31'),
    ('Thoth',    'Database Specialist', 'SQLite, schema design, workflow data',   '2026-03-31');

-- ============================================================
-- SEED: hiring log (founding hires)
-- ============================================================

INSERT INTO hiring_pipeline (role_requested, status, hired_member_id, requested_at, completed_at) VALUES
    ('Senior Researcher',   'completed', 1, '2026-03-31', '2026-03-31'),
    ('HR Agent',            'completed', 2, '2026-03-31', '2026-03-31'),
    ('Database Specialist', 'completed', 3, '2026-03-31', '2026-03-31');
