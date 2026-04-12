from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from pathlib import Path
import anthropic
import os
import subprocess
import threading
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env.team-claude")

app = FastAPI(title="Team Claude")

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR.parent / "team.db"

# ── LinkedIn harvester state ───────────────────────────────────
_harvester_running = False
_harvester_lock = threading.Lock()
_harvester_last_run_at: Optional[str] = None
_harvester_last_run_result: Optional[str] = None  # "ok" | "error" | None

# ── Match scorer state ─────────────────────────────────────────
_scorer_running = False
_scorer_lock = threading.Lock()
_scorer_last_run_at: Optional[str] = None
_scorer_last_run_result: Optional[str] = None  # "ok" | "error" | None


def _run_harvester():
    global _harvester_running, _harvester_last_run_at, _harvester_last_run_result
    harvester_dir = BASE_DIR.parent / "Projects" / "Job Listing Harvester" / "harvester"
    python = harvester_dir / ".venv" / "bin" / "python3"
    try:
        result = subprocess.run(
            [str(python), "harvest.py"],
            cwd=str(harvester_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[harvester] exited {result.returncode}\n{result.stderr}")
        _harvester_last_run_result = "ok" if result.returncode == 0 else "error"
    except Exception as e:
        print(f"[harvester] subprocess error: {e}")
        _harvester_last_run_result = "error"
    finally:
        _harvester_last_run_at = datetime.now(timezone.utc).isoformat()
        with _harvester_lock:
            _harvester_running = False

def _run_scorer():
    global _scorer_running, _scorer_last_run_at, _scorer_last_run_result
    scorer_dir = BASE_DIR.parent / "Projects" / "Job Description Match Score" / "scorer"
    python = scorer_dir / ".venv" / "bin" / "python3"
    try:
        # Always use the latest production prompt version
        rows = query("SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1")
        version = rows[0]["version"] if rows else "v1"
        result = subprocess.run(
            [str(python), "score.py", "--version", version],
            cwd=str(scorer_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[scorer] exited {result.returncode}\n{result.stderr}")
        _scorer_last_run_result = "ok" if result.returncode == 0 else "error"
    except Exception as e:
        print(f"[scorer] subprocess error: {e}")
        _scorer_last_run_result = "error"
    finally:
        _scorer_last_run_at = datetime.now(timezone.utc).isoformat()
        with _scorer_lock:
            _scorer_running = False


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql: str, params: tuple = ()):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/jobs")
async def api_jobs():
    return query("""
        SELECT id, job_board, job_id, company, job_title, location,
               work_type, job_url, status, is_new, first_date_seen,
               source_collection, length(description_text) as desc_length
        FROM jobs
        WHERE archived = 0
        ORDER BY first_date_seen DESC, id DESC
    """)


@app.get("/api/jobs/{job_id}/description", response_class=PlainTextResponse)
async def api_job_description(job_id: int):
    rows = query("SELECT description_text FROM jobs WHERE id=?", (job_id,))
    if not rows or not rows[0]["description_text"]:
        raise HTTPException(status_code=404, detail="No description available")
    return rows[0]["description_text"]


@app.get("/api/roster")
async def api_roster():
    return query("SELECT * FROM team_members ORDER BY date_joined")


@app.get("/api/projects")
async def api_projects():
    return query("SELECT * FROM projects ORDER BY created_at DESC")


@app.get("/api/tasks")
async def api_tasks():
    return query("""
        SELECT t.*,
               tm.name AS assignee_name,
               p.name  AS project_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assigned_to = tm.id
        LEFT JOIN projects p      ON t.project_id  = p.id
        ORDER BY t.created_at DESC
    """)


@app.get("/api/member/{name}/avatar")
async def api_member_avatar(name: str):
    theme_dir = BASE_DIR.parent / "Projects" / "Team Photos" / "themes" / "dossier" / "thumbnails"
    avatar = theme_dir / f"{name.lower()}.webp"
    if not avatar.exists():
        avatar = theme_dir / "placeholder.webp"
    if not avatar.exists():
        raise HTTPException(status_code=404, detail="No avatar available")
    return FileResponse(avatar, media_type="image/webp")


@app.get("/api/member/{name}/avatar/full")
async def api_member_avatar_full(name: str):
    theme_dir = BASE_DIR.parent / "Projects" / "Team Photos" / "themes" / "dossier"
    avatar = theme_dir / f"{name.lower()}.webp"
    if not avatar.exists():
        # fall back to thumbnail
        avatar = theme_dir / "thumbnails" / f"{name.lower()}.webp"
    if not avatar.exists():
        avatar = theme_dir / "thumbnails" / "placeholder.webp"
    if not avatar.exists():
        raise HTTPException(status_code=404, detail="No avatar available")
    return FileResponse(avatar, media_type="image/webp")


@app.get("/api/member/{name}/profile", response_class=PlainTextResponse)
async def api_member_profile(name: str):
    path = BASE_DIR.parent / "Team" / f"{name.lower()}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")
    return path.read_text()


@app.get("/api/hiring/{hiring_id}/brief", response_class=PlainTextResponse)
async def api_hiring_brief(hiring_id: int):
    rows = query("SELECT brief_file FROM hiring_pipeline WHERE id = ?", (hiring_id,))
    if not rows or not rows[0]["brief_file"] or rows[0]["brief_file"] == "founding-member":
        raise HTTPException(status_code=404, detail="No brief available")
    path = BASE_DIR.parent / "Team Inbox" / rows[0]["brief_file"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Brief file not found")
    return path.read_text()


@app.get("/api/scores")
async def api_scores():
    return query("""
        SELECT j.id, j.company, j.job_title, j.location, j.work_type,
               j.job_url, j.apply_flag, j.status, j.job_board,
               s.overall_score, s.skills_score, s.seniority_score, s.work_type_score,
               s.work_arrangement, s.salary_range,
               s.match_summary, s.strengths, s.gaps, s.reasoning, s.recommendation,
               s.score_version, s.scored_at
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id
        WHERE s.score_version = (
            SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1
        )
        AND j.archived = 0
        ORDER BY s.overall_score DESC, j.id
    """)


@app.get("/api/applications")
async def api_applications():
    return query("""
        SELECT a.id, a.company, a.job_title, a.status, a.apply_date,
               a.contact, a.notes, a.cover_letter, a.application_link, a.salary_range_top,
               a.resume_link, a.job_id, a.job_board, a.board_job_id,
               j.id      AS jobs_db_id,
               j.job_url AS job_url,
               s.overall_score,
               CASE WHEN ic.id IS NOT NULL THEN 1 ELSE 0 END AS is_interesting_company
        FROM applications a
        LEFT JOIN jobs j
               ON a.job_board   = j.job_board
              AND a.board_job_id = j.job_id
        LEFT JOIN job_scores s
               ON j.id = s.job_id
              AND s.score_version = (
                  SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1
              )
        LEFT JOIN interesting_companies ic
               ON LOWER(a.company) = LOWER(ic.name)
        ORDER BY a.apply_date DESC, a.id DESC
    """)


@app.patch("/api/jobs/{job_id}/status")
async def update_job_status(job_id: int, payload: dict = Body(...)):
    status = payload.get("status")
    if status not in ("new", "scored", "skip", "duplicate"):
        raise HTTPException(status_code=400, detail="invalid status")
    conn = get_conn()
    conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/jobs/archive")
async def archive_jobs(payload: dict = Body(...)):
    ids = payload.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="no ids provided")
    placeholders = ",".join("?" * len(ids))
    conn = get_conn()
    conn.execute(f"UPDATE jobs SET archived=1 WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()
    return {"ok": True, "archived": len(ids)}


@app.patch("/api/applications/{app_id}")
async def update_application(app_id: int, payload: dict = Body(...)):
    allowed = {k: v for k, v in payload.items() if k in ("status", "notes", "cover_letter")}
    if not allowed:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    sets = ", ".join(f"{k}=?" for k in allowed)
    vals = list(allowed.values()) + [app_id]
    conn = get_conn()
    conn.execute(f"UPDATE applications SET {sets}, updated_at=datetime('now') WHERE id=?", vals)
    conn.commit()
    conn.close()
    return {"ok": True}


VOICE_OF_TIM_SKILL_ID = os.environ.get("VOICE_OF_TIM_SKILL_ID")


def generate_cover_letter(app_id: int, company: str, job_title: str,
                           description_text: str, match_summary: str, strengths: str):
    try:
        # Load prompt from DB — use latest version
        conn = get_conn()
        prompt_row = conn.execute(
            "SELECT system_prompt, user_prompt_template, model FROM cover_letter_prompts "
            "ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        conn.close()

        if not prompt_row:
            return

        user_prompt = prompt_row["user_prompt_template"].format(
            company=company,
            job_title=job_title,
            description_text=description_text[:8000],
            match_summary=match_summary,
            strengths=strengths,
        )

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # v2+: use voice-of-tim skill via skills beta API
        # Falls back to standard API call if skills beta is unavailable
        try:
            message = client.beta.messages.create(
                model=prompt_row["model"],
                max_tokens=1024,
                betas=["code-execution-2025-08-25", "skills-2025-10-02"],
                system=prompt_row["system_prompt"],
                container={
                    "skills": [
                        {"type": "custom", "skill_id": VOICE_OF_TIM_SKILL_ID, "version": "latest"}
                    ]
                },
                messages=[{"role": "user", "content": user_prompt}],
                tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            )
        except Exception as skill_err:
            print(f"[cover_letter] skills beta unavailable, falling back to standard API: {skill_err}")
            message = client.messages.create(
                model=prompt_row["model"],
                max_tokens=1024,
                system=prompt_row["system_prompt"],
                messages=[{"role": "user", "content": user_prompt}],
            )

        cover_letter_text = message.content[0].text

        # Write result back to applications
        conn = get_conn()
        conn.execute(
            "UPDATE applications SET cover_letter=?, updated_at=datetime('now') WHERE id=?",
            (cover_letter_text, app_id)
        )
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"[cover_letter] generation failed for app {app_id}: {e}")


@app.post("/api/jobs/{job_id}/apply/{value}")
async def set_apply_flag(job_id: int, value: int, background_tasks: BackgroundTasks):
    conn = get_conn()

    # Always update apply_flag on the jobs table
    conn.execute("UPDATE jobs SET apply_flag=? WHERE id=?", (1 if value else 0, job_id))
    conn.commit()

    if value:
        # Check if application already exists for this job
        existing = conn.execute(
            "SELECT id FROM applications WHERE job_id=?", (job_id,)
        ).fetchone()

        if not existing:
            # Pull everything we need from jobs + job_scores
            job = conn.execute("""
                SELECT j.id, j.company, j.job_title, j.job_board, j.job_id AS board_job_id,
                       j.description_text,
                       s.match_summary, s.strengths, s.salary_range
                FROM jobs j
                LEFT JOIN job_scores s ON j.id = s.job_id
                    AND s.score_version = (
                        SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1
                    )
                WHERE j.id = ?
            """, (job_id,)).fetchone()

            if job:
                conn.execute("""
                    INSERT INTO applications
                        (job_id, company, job_title, status, apply_date,
                         job_board, board_job_id, match_assessment, salary_range_top, source)
                    VALUES (?, ?, ?, 'new', NULL, ?, ?, ?, ?, 'harvested')
                """, (
                    job_id,
                    job["company"],
                    job["job_title"],
                    job["job_board"],
                    job["board_job_id"],
                    job["match_summary"],
                    job["salary_range"],
                ))
                conn.commit()

                app_id = conn.execute(
                    "SELECT id FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
                ).fetchone()["id"]

                # Queue cover letter generation as a background task
                background_tasks.add_task(
                    generate_cover_letter,
                    app_id=app_id,
                    company=job["company"],
                    job_title=job["job_title"],
                    description_text=job["description_text"] or "",
                    match_summary=job["match_summary"] or "",
                    strengths=job["strengths"] or "",
                )

    conn.close()
    return {"ok": True}


@app.get("/api/hiring")
async def api_hiring():
    return query("""
        SELECT h.*,
               tm.name AS hired_name
        FROM hiring_pipeline h
        LEFT JOIN team_members tm ON h.hired_member_id = tm.id
        ORDER BY h.requested_at DESC
    """)


# ── Match Scorer ───────────────────────────────────────────────

@app.post("/api/score/run")
async def start_scorer():
    global _scorer_running
    with _scorer_lock:
        if _scorer_running:
            raise HTTPException(status_code=409, detail="already_running")
        _scorer_running = True

    t = threading.Thread(target=_run_scorer, daemon=True)
    t.start()
    return {"status": "started"}


@app.get("/api/score/status")
async def scorer_status():
    with _scorer_lock:
        running = _scorer_running
    return {
        "status": "running" if running else "idle",
        "last_run_at": _scorer_last_run_at,
        "last_run_result": _scorer_last_run_result,
    }


@app.get("/api/score/progress")
async def score_progress():
    """Returns scored/total counts for unapplied jobs under the latest prompt version."""
    rows = query("SELECT version FROM score_prompts ORDER BY created_at DESC LIMIT 1")
    if not rows:
        return {"scored": 0, "total": 0, "version": None}
    version = rows[0]["version"]
    scored = query("""
        SELECT COUNT(*) AS cnt FROM jobs j
        JOIN job_scores s ON j.id = s.job_id AND s.score_version = ?
        WHERE j.description_text IS NOT NULL
          AND length(j.description_text) > 100
          AND j.id NOT IN (SELECT job_id FROM applications WHERE job_id IS NOT NULL)
    """, (version,))[0]["cnt"]
    total = query("""
        SELECT COUNT(*) AS cnt FROM jobs j
        WHERE j.description_text IS NOT NULL
          AND length(j.description_text) > 100
          AND j.id NOT IN (SELECT job_id FROM applications WHERE job_id IS NOT NULL)
    """)[0]["cnt"]
    return {"scored": scored, "total": total, "version": version}


# ── LinkedIn Harvester ─────────────────────────────────────────

@app.post("/api/harvest/linkedin")
async def start_linkedin_harvest():
    global _harvester_running
    with _harvester_lock:
        if _harvester_running:
            raise HTTPException(status_code=409, detail="already_running")
        _harvester_running = True

    t = threading.Thread(target=_run_harvester, daemon=True)
    t.start()
    return {"status": "started"}


@app.get("/api/harvest/linkedin/status")
async def linkedin_harvest_status():
    with _harvester_lock:
        running = _harvester_running
    return {
        "status": "running" if running else "idle",
        "last_run_at": _harvester_last_run_at,
        "last_run_result": _harvester_last_run_result,
    }
