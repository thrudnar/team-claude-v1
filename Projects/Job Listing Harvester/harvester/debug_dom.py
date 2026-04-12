"""
debug_dom.py — Argus deep DOM inspection
Looks for job IDs in data attributes, entity URNs, and JS state.
Runs headed so we see the actual page.

Usage:
    python debug_dom.py
"""

import asyncio
import re
import json
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE = Path(__file__).parent.parent / "browser-profile"
URL     = "https://www.linkedin.com/jobs/collections/top-applicant/"


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=False,
            args=["--start-maximized"],
        )
        page = await ctx.new_page()
        print(f"Loading: {URL}")
        await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        # 1. All hrefs containing job-related patterns
        print("\n── href patterns ──")
        hrefs = await page.evaluate("""
            () => [...document.querySelectorAll('a[href]')]
                .map(a => a.href)
                .filter(h => h.includes('job') || h.includes('Job'))
                .slice(0, 30)
        """)
        for h in hrefs:
            print(f"  {h}")

        # 2. data-job-id attributes
        print("\n── data-job-id ──")
        job_ids = await page.evaluate("""
            () => [...document.querySelectorAll('[data-job-id]')]
                .map(el => el.getAttribute('data-job-id'))
        """)
        print(f"  Found {len(job_ids)}: {job_ids}")

        # 3. data-entity-urn (LinkedIn's standard URN pattern)
        print("\n── data-entity-urn (jobPosting) ──")
        urns = await page.evaluate("""
            () => [...document.querySelectorAll('[data-entity-urn]')]
                .map(el => el.getAttribute('data-entity-urn'))
                .filter(u => u && u.includes('jobPosting'))
        """)
        print(f"  Found {len(urns)}: {urns[:10]}")

        # 4. data-occludable-job-id
        print("\n── data-occludable-job-id ──")
        occ = await page.evaluate("""
            () => [...document.querySelectorAll('[data-occludable-job-id]')]
                .map(el => el.getAttribute('data-occludable-job-id'))
        """)
        print(f"  Found {len(occ)}: {occ}")

        # 5. Any attribute containing a 10-digit number (job ID pattern)
        print("\n── all attrs with job-ID-like values ──")
        attrs = await page.evaluate("""
            () => {
                const results = [];
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    for (const attr of el.attributes) {
                        if (/^\\d{9,12}$/.test(attr.value)) {
                            results.push({tag: el.tagName, attr: attr.name, val: attr.value});
                        }
                    }
                }
                return results.slice(0, 20);
            }
        """)
        for a in attrs:
            print(f"  <{a['tag']} {a['attr']}={a['val']}>")

        # 6. Page source scan for job IDs
        print("\n── page source job ID scan ──")
        source = await page.content()
        ids = set(re.findall(r'"jobPostingId["\s:]+(\d{9,12})', source))
        ids |= set(re.findall(r'jobPosting:(\d{9,12})', source))
        ids |= set(re.findall(r'currentJobId[="\s:]+(\d{9,12})', source))
        print(f"  Found {len(ids)} IDs in source: {sorted(ids)}")

        await ctx.close()
        print("\n── DOM inspection complete ──")


if __name__ == "__main__":
    asyncio.run(main())
