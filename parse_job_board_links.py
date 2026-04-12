"""
parse_job_board_links.py

Task 3: Parse Job Board Links from spreadsheet and update applications table
with job_board and job_id values.
"""

import sqlite3
import openpyxl
from urllib.parse import urlparse, parse_qs
import re
from collections import defaultdict


DB_PATH = "team.db"
XLSX_PATH = "Team Inbox/job_applications_log.xlsx"


def parse_job_board_link(raw_url):
    """
    Parse a job board URL and return (job_board, job_id).
    Returns (None, None) if unparseable.
    """
    if not raw_url:
        return None, None

    raw = str(raw_url).strip()
    if not raw.startswith("http"):
        # Plain text label — extract board name if possible
        lower = raw.lower()
        if "linkedin" in lower:
            return "linkedin", None
        if "jobright" in lower:
            return "jobright", None
        if "indeed" in lower:
            return "indeed", None
        # Other plain text (e.g. "email", "Jobright.ai") — not a URL
        return None, None

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    qs = parse_qs(parsed.query)

    # --- LinkedIn ---
    if "linkedin.com" in host:
        job_board = "linkedin"
        job_id = None

        # Pattern: /jobs/view/1234567890/
        m = re.search(r"/jobs/view/(\d+)", parsed.path)
        if m:
            job_id = m.group(1)
        else:
            # Pattern: ?currentJobId=1234567890
            cjid = qs.get("currentJobId", [None])[0]
            if cjid and cjid.isdigit():
                job_id = cjid
            else:
                # Try to extract any numeric ID from the path
                m2 = re.search(r"/(\d{8,})", parsed.path)
                if m2:
                    job_id = m2.group(1)

        return job_board, job_id

    # --- Indeed ---
    if "indeed.com" in host:
        job_board = "indeed"
        job_id = qs.get("jk", [None])[0]
        if not job_id:
            # Try path-based extraction
            m = re.search(r"/([a-f0-9]{16})", parsed.path)
            if m:
                job_id = m.group(1)
        return job_board, job_id

    # --- Jobright ---
    if "jobright.ai" in host:
        job_board = "jobright"
        # Pattern: /jobs/info/<hex_id>
        m = re.search(r"/jobs/info/([a-f0-9]+)", parsed.path)
        job_id = m.group(1) if m else None
        return job_board, job_id

    # --- Greenhouse ---
    if "greenhouse.io" in host:
        job_board = "greenhouse"
        # Pattern: /jobs/1234567890 or /jobs/1234567890?...
        m = re.search(r"/jobs/(\d+)", parsed.path)
        job_id = m.group(1) if m else None
        return job_board, job_id

    # --- Lever ---
    if "lever.co" in host:
        job_board = "lever"
        # Pattern: /<company>/<uuid>
        m = re.search(r"/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", parsed.path, re.I)
        job_id = m.group(1) if m else None
        return job_board, job_id

    # --- Workday ---
    if "workday.com" in host or "myworkdayjobs.com" in host:
        return "workday", None

    # --- Ashby ---
    if "ashbyhq.com" in host:
        job_board = "ashby"
        # Pattern: /<company>/<uuid>
        m = re.search(r"/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", parsed.path, re.I)
        job_id = m.group(1) if m else None
        return job_board, job_id

    # --- Dayforce / Ceridian ---
    if "dayforcehcm.com" in host:
        job_board = "dayforce"
        # Pattern: /jobs/<id>
        m = re.search(r"/jobs/(\d+)", parsed.path)
        job_id = m.group(1) if m else None
        return job_board, job_id

    # --- Builtin ---
    if "builtin.com" in host:
        return "builtin", None

    # --- ActBlue ---
    if "actblue.com" in host:
        job_board = "actblue"
        job_id = qs.get("gh_jid", [None])[0]
        return job_board, job_id

    # --- Generic: extract domain keyword as job_board ---
    # Strip www., extract root domain name
    domain_parts = host.replace("www.", "").split(".")
    # Use the primary domain name (first meaningful part)
    job_board = domain_parts[0] if domain_parts else None
    return job_board, None


def load_spreadsheet_rows():
    """Load data rows from spreadsheet, skipping blank rows (Num is None)."""
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    data = []
    for row in rows[1:]:  # skip header
        num = row[0]
        if num is None:
            continue
        apply_date_raw = row[2]
        job_board_link = row[3]
        company = row[4]
        job_title = row[5]

        # Normalise apply_date to YYYY-MM-DD string
        if hasattr(apply_date_raw, "strftime"):
            apply_date = apply_date_raw.strftime("%Y-%m-%d")
        elif apply_date_raw:
            apply_date = str(apply_date_raw)[:10]
        else:
            apply_date = None

        # Strip trailing/leading whitespace from text fields
        company = company.strip() if company else company
        job_title = job_title.strip() if job_title else job_title

        data.append({
            "num": int(num),
            "apply_date": apply_date,
            "company": company,
            "job_title": job_title,
            "job_board_link": job_board_link,
        })

    wb.close()
    return data


def main():
    ss_rows = load_spreadsheet_rows()
    print(f"Spreadsheet data rows loaded: {len(ss_rows)}")

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Load all DB applications keyed by (company, job_title, apply_date)
    cur.execute("SELECT id, company, job_title, apply_date FROM applications ORDER BY id")
    db_rows = cur.fetchall()
    print(f"DB applications loaded: {len(db_rows)}")

    # Build lookup: (company, job_title, apply_date) -> list of db ids
    db_lookup = defaultdict(list)
    for row in db_rows:
        key = (row["company"], row["job_title"], row["apply_date"])
        db_lookup[key].append(row["id"])

    # Also build (company, job_title) -> list of (apply_date, id) for tiebreaking
    db_lookup_2key = defaultdict(list)
    for row in db_rows:
        db_lookup_2key[(row["company"], row["job_title"])].append((row["apply_date"], row["id"]))

    # Process each spreadsheet row
    updates = []
    matched = 0
    unmatched = 0
    parseable_board = 0
    parseable_id = 0
    board_counts = defaultdict(int)

    for ss_row in ss_rows:
        raw_url = ss_row["job_board_link"]
        job_board, job_id = parse_job_board_link(raw_url)

        # Find matching DB row
        key3 = (ss_row["company"], ss_row["job_title"], ss_row["apply_date"])
        db_ids = db_lookup.get(key3, [])

        if len(db_ids) == 1:
            db_id = db_ids[0]
        elif len(db_ids) > 1:
            # Should be rare — take the first
            db_id = db_ids[0]
            print(f"  WARN: multiple exact matches for {key3}, using id={db_id}")
        else:
            # Try (company, job_title) only — match by closest apply_date
            candidates = db_lookup_2key.get((ss_row["company"], ss_row["job_title"]), [])
            if candidates:
                # Pick closest apply_date
                candidates.sort(key=lambda x: x[0] or "")
                db_id = candidates[0][1]
                print(f"  WARN: no exact date match for {ss_row['company']} / {ss_row['job_title']} / {ss_row['apply_date']}, using id={db_id} (date={candidates[0][0]})")
            else:
                unmatched += 1
                print(f"  UNMATCHED: num={ss_row['num']} {ss_row['company']} / {ss_row['job_title']}")
                continue

        matched += 1

        if job_board:
            parseable_board += 1
            board_counts[job_board] += 1
        if job_id:
            parseable_id += 1

        updates.append((job_board, job_id, db_id))

    # Execute updates
    cur.executemany(
        "UPDATE applications SET job_board = ?, job_id = ? WHERE id = ?",
        updates
    )
    conn.commit()
    conn.close()

    print(f"\n--- Summary ---")
    print(f"Spreadsheet rows processed: {len(ss_rows)}")
    print(f"Matched to DB rows:         {matched}")
    print(f"Unmatched (skipped):        {unmatched}")
    print(f"DB updates written:         {len(updates)}")
    print(f"Rows with parseable job_board: {parseable_board}")
    print(f"Rows with extracted job_id:    {parseable_id}")
    print(f"\nBreakdown by job_board:")
    for board, cnt in sorted(board_counts.items(), key=lambda x: -x[1]):
        print(f"  {cnt:4d}  {board}")


if __name__ == "__main__":
    main()
