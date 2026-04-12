"""
score_test.py — Thoth: Scoring Prompt Test Runner
Scores a set of jobs against a specified prompt version and writes results
to score_tests (not job_scores), allowing safe comparison across prompt versions.

Usage:
    python score_test.py [--version v2] [--jobs 1,2,3] [--dry-run]

Requirements:
    pip install anthropic
    ANTHROPIC_API_KEY must be set in environment.
"""

import sqlite3
import json
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

DB_PATH = Path(__file__).parent.parent.parent.parent / "team.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_prompt(conn, version: str):
    row = conn.execute(
        "SELECT * FROM score_prompts WHERE version = ?", (version,)
    ).fetchone()
    if not row:
        print(f"Error: no prompt found for version '{version}'")
        sys.exit(1)
    return row


def get_default_jobs(conn, limit: int = 30):
    """Return top N jobs by overall_score from job_scores where score_version='v1'."""
    query = """
        SELECT j.id, j.company, j.job_title, j.description_text,
               j.work_type, j.location, j.job_url
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id AND s.score_version = 'v1'
        WHERE j.description_text IS NOT NULL
          AND length(j.description_text) > 100
        ORDER BY s.overall_score DESC
        LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()


def get_jobs_by_ids(conn, job_ids: list):
    """Return specific jobs by their IDs."""
    placeholders = ",".join("?" * len(job_ids))
    query = f"""
        SELECT id, company, job_title, description_text,
               work_type, location, job_url
        FROM jobs
        WHERE id IN ({placeholders})
          AND description_text IS NOT NULL
          AND length(description_text) > 100
        ORDER BY id
    """
    return conn.execute(query, job_ids).fetchall()


def call_claude(client, prompt_row, job) -> dict:
    user_msg = prompt_row["user_prompt_template"].format(
        description_text=job["description_text"]
    )
    response = client.messages.create(
        model=prompt_row["model"],
        max_tokens=4096,
        system=prompt_row["system_prompt"],
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if the model adds them despite instructions
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])  # drop first line
        raw = raw.rsplit("```", 1)[0]         # drop closing fence
    return json.loads(raw.strip())


def insert_test_score(conn, job_id: int, version: str, model: str, result: dict):
    conn.execute("""
        INSERT INTO score_tests
            (job_id, prompt_version, model,
             overall_score, skills_score, seniority_score, work_type_score,
             work_arrangement, salary_range,
             match_summary, strengths, gaps, recommendation,
             scored_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(job_id, prompt_version) DO UPDATE SET
            model                = excluded.model,
            overall_score        = excluded.overall_score,
            skills_score         = excluded.skills_score,
            seniority_score      = excluded.seniority_score,
            work_type_score      = excluded.work_type_score,
            work_arrangement     = excluded.work_arrangement,
            salary_range         = excluded.salary_range,
            match_summary        = excluded.match_summary,
            strengths            = excluded.strengths,
            gaps                 = excluded.gaps,
            recommendation       = excluded.recommendation,
            scored_at            = excluded.scored_at
    """, (
        job_id, version, model,
        result.get("overall_score"),
        result.get("skills_score"),
        result.get("seniority_score"),
        result.get("work_type_score"),
        result.get("work_arrangement"),
        result.get("salary_range"),
        result.get("match_summary"),
        result.get("strengths"),
        result.get("gaps"),
        result.get("recommendation"),
        datetime.now().isoformat(),
    ))
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Call API and print results but don't write to DB")
    parser.add_argument("--version", default="v2",
                        help="Prompt version to test (default: v2)")
    parser.add_argument("--jobs", type=str, default=None,
                        help="Comma-separated list of job IDs to score "
                             "(default: top 30 by overall_score from job_scores v1)")
    args = parser.parse_args()

    conn = get_db()
    prompt_row = load_prompt(conn, args.version)

    if args.jobs:
        try:
            job_ids = [int(x.strip()) for x in args.jobs.split(",")]
        except ValueError:
            print("Error: --jobs must be a comma-separated list of integers")
            sys.exit(1)
        jobs = get_jobs_by_ids(conn, job_ids)
    else:
        jobs = get_default_jobs(conn, limit=30)

    print(f"Prompt : {args.version}  |  Model: {prompt_row['model']}")
    print(f"Target : score_tests table")
    print(f"To score: {len(jobs)} jobs")
    if args.dry_run:
        print("Mode   : dry-run (results printed, nothing written)")
    print()

    if not jobs:
        print("Nothing to score — no matching jobs found.")
        conn.close()
        return

    client = anthropic.Anthropic()
    scored = 0
    errors = 0

    for i, job in enumerate(jobs, 1):
        label = f"{job['job_title'] or '?'} @ {job['company'] or '?'}"
        print(f"[{i}/{len(jobs)}] {label}")

        try:
            result = call_claude(client, prompt_row, job)

            overall = result.get("overall_score", "?")
            rec     = result.get("recommendation", "?")
            arr     = result.get("work_arrangement", "?")
            sal     = result.get("salary_range", "Not stated")
            summary = (result.get("match_summary") or "")[:120]

            print(f"  {overall:>3}  {rec:<12}  {arr:<12}  {sal}")
            print(f"  {summary}")

            if not args.dry_run:
                insert_test_score(conn, job["id"], args.version, prompt_row["model"], result)
            scored += 1

        except json.JSONDecodeError as e:
            print(f"  [error] JSON parse failed: {e}")
            errors += 1
        except anthropic.APIError as e:
            print(f"  [error] API error: {e}")
            errors += 1
        except Exception as e:
            print(f"  [error] {e}")
            errors += 1

        # Polite pause to avoid rate-limit bursts on large runs
        if i < len(jobs):
            time.sleep(0.3)

    conn.close()
    print(f"\n── Done ──")
    print(f"  Scored : {scored}")
    print(f"  Errors : {errors}")
    if args.dry_run:
        print("  (dry-run — nothing written to DB)")


if __name__ == "__main__":
    main()
