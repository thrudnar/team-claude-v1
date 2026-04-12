"""
score.py — Prospero: Job Description Match Scorer
Reads unscored jobs from team.db, calls Claude with the active prompt version,
writes structured scores to job_scores.

Usage:
    python score.py [--dry-run] [--limit N] [--version v1]

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
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env.team-claude")

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


def get_unscored_jobs(conn, version: str, limit: int = None, unapplied_only: bool = False):
    query = """
        SELECT j.id, j.company, j.job_title, j.description_text,
               j.work_type, j.location, j.job_url
        FROM jobs j
        LEFT JOIN job_scores s ON j.id = s.job_id AND s.score_version = ?
        WHERE s.id IS NULL
          AND j.description_text IS NOT NULL
          AND length(j.description_text) > 100
    """
    if unapplied_only:
        query += """
          AND j.id NOT IN (
              SELECT job_id FROM applications WHERE job_id IS NOT NULL
          )
        """
    query += " ORDER BY j.id"
    if limit:
        query += f" LIMIT {int(limit)}"
    return conn.execute(query, (version,)).fetchall()


def call_claude(client, prompt_row, job, max_retries: int = 4) -> dict:
    user_msg = prompt_row["user_prompt_template"].format(
        description_text=job["description_text"]
    )
    delay = 5
    for attempt in range(max_retries):
        try:
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
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            print(f"  [rate limit] waiting {delay}s before retry {attempt + 1}/{max_retries - 1}…")
            time.sleep(delay)
            delay *= 2


def insert_score(conn, job_id: int, version: str, result: dict):
    conn.execute("""
        INSERT INTO job_scores
            (job_id, score_version,
             overall_score, skills_score, seniority_score, work_type_score,
             work_arrangement, salary_range,
             match_summary, strengths, gaps, recommendation,
             scored_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(job_id, score_version) DO UPDATE SET
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
        job_id, version,
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
    conn.execute(
        "UPDATE jobs SET status='scored' WHERE id=? AND status='new'",
        (job_id,)
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Call API and print results but don't write to DB")
    parser.add_argument("--limit", type=int,
                        help="Max number of jobs to score in this run")
    parser.add_argument("--version", default="v1",
                        help="Prompt version to use (default: v1)")
    parser.add_argument("--unapplied", action="store_true",
                        help="Only score jobs that have no application row")
    args = parser.parse_args()

    conn = get_db()
    prompt_row = load_prompt(conn, args.version)
    jobs = get_unscored_jobs(conn, args.version, args.limit, args.unapplied)

    print(f"Prompt : {args.version}  |  Model: {prompt_row['model']}")
    print(f"To score: {len(jobs)} jobs")
    if args.dry_run:
        print("Mode   : dry-run (results printed, nothing written)")
    print()

    if not jobs:
        print("Nothing to score — all jobs already have scores for this version.")
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
                insert_score(conn, job["id"], args.version, result)
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

        # Pause between requests (Tier 2: 450k input tokens/min)
        if i < len(jobs):
            time.sleep(0.5)

    conn.close()
    print(f"\n── Done ──")
    print(f"  Scored : {scored}")
    print(f"  Errors : {errors}")
    if args.dry_run:
        print("  (dry-run — nothing written to DB)")


if __name__ == "__main__":
    main()
