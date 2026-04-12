# ERD — team.db (Team Management Schema)

Last updated: 2026-04-02

---

## team_members
- PK  id
-     name
-     role
-     domain
-     status
-     model
-     date_joined

## projects
- PK  id
-     name
-     description
-     status
-     created_at

## tasks
- PK  id
- FK  project_id → projects.id
- FK  assigned_to → team_members.id
-     title
-     description
-     status
-     priority
-     created_at
-     updated_at

## hiring_pipeline
- PK  id
- FK  hired_member_id → team_members.id
-     role_requested
-     brief_file
-     status
-     requested_at
-     completed_at

## work_log
- PK  id
- FK  task_id → tasks.id
- FK  team_member_id → team_members.id
-     action
-     notes
-     logged_at
