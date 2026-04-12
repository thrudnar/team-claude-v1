"""
debug_session.py — Argus diagnostic tool
Opens each collection URL in a HEADED browser, counts job links found,
and saves a screenshot for inspection.

Usage:
    python debug_session.py
"""

import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE    = Path(__file__).parent.parent / "browser-profile"
SCREENSHOTS = Path(__file__).parent.parent / "debug-screenshots"

COLLECTIONS = [
    ("top-applicant", "https://www.linkedin.com/jobs/collections/top-applicant/"),
    ("recommended",   "https://www.linkedin.com/jobs/collections/recommended/"),
    ("remote-jobs",   "https://www.linkedin.com/jobs/collections/remote-jobs/"),
]

def extract_job_id(url: str):
    m = re.search(r'(?:/jobs/view/|currentJobId=)(\d+)', url)
    return m.group(1) if m else None


async def main():
    SCREENSHOTS.mkdir(exist_ok=True)

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=False,
            args=["--start-maximized"],
        )
        page = await ctx.new_page()

        for name, url in COLLECTIONS:
            print(f"\n── {name} ──")
            print(f"  Loading: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)  # let page settle fully

            # Count all job links
            links = await page.query_selector_all("a[href*='/jobs/view/'], a[href*='currentJobId=']")
            job_ids = set()
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    jid = extract_job_id(href)
                    if jid:
                        job_ids.add(jid)

            print(f"  Job links found: {len(job_ids)}")
            for jid in sorted(job_ids):
                print(f"    {jid}")

            # Screenshot
            shot_path = SCREENSHOTS / f"{name}.png"
            await page.screenshot(path=str(shot_path), full_page=True)
            print(f"  Screenshot saved: {shot_path}")

        await ctx.close()
        print("\n── Debug complete ──")


if __name__ == "__main__":
    asyncio.run(main())
