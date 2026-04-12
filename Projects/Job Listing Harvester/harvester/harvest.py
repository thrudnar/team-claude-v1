"""
harvest.py — Argus: LinkedIn Job Collection Harvester
Scrapes LinkedIn job collection pages using a persistent authenticated session.
Writes new jobs to the jobs table in team.db.

Usage:
    python harvest.py [--dry-run]
"""

import asyncio
import sqlite3
import re
import argparse
import sys
from datetime import date
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ── Paths ─────────────────────────────────────────────────────
BASE       = Path(__file__).parent
PROFILE    = BASE.parent / "browser-profile"
DB_PATH    = BASE.parent.parent.parent / "team.db"

COLLECTIONS = [
    ("top-applicant", "https://www.linkedin.com/jobs/collections/top-applicant/"),
    ("recommended",   "https://www.linkedin.com/jobs/collections/recommended/"),
    ("remote-jobs",   "https://www.linkedin.com/jobs/collections/remote-jobs/"),
]

JOB_BOARD  = "LinkedIn"
SCROLL_PAUSE     = 2.0   # seconds between scrolls
PAGE_DELAY       = 3.0   # seconds between job page fetches
MAX_JOBS_PER_URL = 100   # cap on job IDs collected per collection URL


# ── DB ────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def job_exists(conn, job_id: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM jobs WHERE job_board=? AND job_id=?",
        (JOB_BOARD, job_id)
    ).fetchone() is not None

def insert_job(conn, data: dict, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] Would insert: {data['job_id']} — {data['job_title']} @ {data['company']}")
        return
    today = date.today().isoformat()
    conn.execute("""
        INSERT INTO jobs
            (job_board, job_id, company, job_title, location, work_type,
             job_url, description_text, source_collection,
             first_date_seen, most_recent_date_seen, is_new, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,1,'new')
        ON CONFLICT(job_board, job_id) DO UPDATE SET
            most_recent_date_seen=excluded.most_recent_date_seen
    """, (
        JOB_BOARD,
        data["job_id"],
        data.get("company"),
        data.get("job_title"),
        data.get("location"),
        data.get("work_type"),
        data.get("job_url"),
        data.get("description_text"),
        data.get("source_collection"),
        today, today,
    ))
    conn.commit()


# ── Helpers ───────────────────────────────────────────────────
def extract_job_id(url: str):
    m = re.search(r'(?:/jobs/view/|currentJobId=)(\d+)', url)
    return m.group(1) if m else None

def detect_work_type(text: str) -> str:
    t = (text or "").lower()
    if "remote" in t:   return "remote"
    if "hybrid" in t:   return "hybrid"
    if "on-site" in t or "onsite" in t: return "onsite"
    return "unknown"


# ── Scraping ──────────────────────────────────────────────────
async def get_job_ids_from_collection(page, url: str, max_jobs: int = MAX_JOBS_PER_URL) -> list[dict]:
    """Load a collection page and paginate via the Next button until max_jobs IDs are collected."""
    print(f"  Loading: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)
    except PWTimeout:
        print(f"  [warn] Timeout loading {url} — skipping")
        return []

    seen_ids: set[str] = set()
    page_num = 1

    while True:
        current_ids = await page.evaluate("""
            () => [...new Set(
                [...document.querySelectorAll('[data-occludable-job-id]')]
                .map(el => el.getAttribute('data-occludable-job-id'))
                .filter(Boolean)
            )]
        """)
        seen_ids.update(current_ids)
        print(f"  Page {page_num}: {len(current_ids)} IDs ({len(seen_ids)} total so far)")

        if len(seen_ids) >= max_jobs:
            print(f"  Reached cap of {max_jobs}")
            break

        # LinkedIn collections use a Next button (not infinite scroll)
        next_btn = await page.query_selector("button.artdeco-button--icon-right")
        if not next_btn:
            print(f"  No Next button — end of list")
            break
        if not await next_btn.is_visible() or not await next_btn.is_enabled():
            print(f"  Next button disabled — end of list")
            break

        await next_btn.click()
        await asyncio.sleep(PAGE_DELAY)
        page_num += 1

    result_ids = list(seen_ids)[:max_jobs]
    print(f"  Collected {len(result_ids)} job IDs across {page_num} page(s)")
    return [{"job_id": jid, "job_url": f"https://www.linkedin.com/jobs/view/{jid}/"} for jid in result_ids]


async def get_job_details(page, job_url: str) -> dict:
    """Fetch a job's detail page and extract structured fields."""
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
    except PWTimeout:
        print(f"    [warn] Timeout on {job_url}")
        return {}

    async def text(selector):
        el = await page.query_selector(selector)
        return (await el.inner_text()).strip() if el else None

    job_title = await text("h1.t-24, h1.jobs-unified-top-card__job-title, h1")
    company   = await text("a.app-aware-link[href*='linkedin.com/company'], .jobs-unified-top-card__company-name a, .job-details-jobs-unified-top-card__company-name a")

    # Location — first tvm__text--low-emphasis that isn't a separator dot
    location = None
    for el in await page.query_selector_all("span.tvm__text--low-emphasis"):
        t = (await el.inner_text()).strip()
        if t and t != "·":
            location = t
            break

    # Description
    desc_el = await page.query_selector(".jobs-description__content, .job-details-jobs-unified-top-card__job-description")
    description_text = (await desc_el.inner_text()).strip() if desc_el else None

    # Work type — check tvm__text spans first (Remote/Hybrid/On-site appear there),
    # then fall back to description text
    work_type_raw = ""
    for el in await page.query_selector_all("span.tvm__text"):
        t = (await el.inner_text()).strip()
        if any(k in t.lower() for k in ["remote", "hybrid", "on-site", "onsite"]):
            work_type_raw = t
            break
    work_type = detect_work_type(work_type_raw or description_text or "")

    return {
        "job_title":        job_title,
        "company":          company,
        "location":         location,
        "work_type":        work_type,
        "description_text": description_text,
    }


# ── Main ──────────────────────────────────────────────────────
async def run(dry_run: bool):
    if not PROFILE.exists():
        print("No browser profile found.")
        print("Run setup_session.py first to log into LinkedIn.")
        sys.exit(1)

    conn = get_db()
    total_new = 0
    total_seen = 0

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=True,
            viewport={"width": 1280, "height": 1800},
        )
        page = await ctx.new_page()

        for collection_name, collection_url in COLLECTIONS:
            print(f"\n── Collection: {collection_name} ──")
            job_stubs = await get_job_ids_from_collection(page, collection_url)

            new_jobs = []
            for stub in job_stubs:
                if job_exists(conn, stub["job_id"]):
                    total_seen += 1
                else:
                    new_jobs.append(stub)

            print(f"  {len(new_jobs)} new / {len(job_stubs) - len(new_jobs)} already in DB")

            for stub in new_jobs:
                print(f"  Fetching: {stub['job_url']}")
                details = await get_job_details(page, stub["job_url"])
                await asyncio.sleep(PAGE_DELAY)

                data = {**stub, **details, "source_collection": collection_name}
                insert_job(conn, data, dry_run)

                label = f"{details.get('job_title','?')} @ {details.get('company','?')}"
                print(f"  {'[dry-run] ' if dry_run else ''}Stored: {label}")
                total_new += 1

        await ctx.close()

    conn.close()
    print(f"\n── Done ──")
    print(f"  New jobs stored : {total_new}")
    print(f"  Already in DB   : {total_seen}")
    if dry_run:
        print("  (dry-run — nothing written)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Scrape but don't write to DB")
    args = parser.parse_args()
    asyncio.run(run(args.dry_run))
