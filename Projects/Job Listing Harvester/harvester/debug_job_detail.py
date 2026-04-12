"""
debug_job_detail.py — Argus job detail DOM inspector
Opens a real LinkedIn job detail page and probes for location/work_type selectors.
Runs headed so the page renders fully.

Usage:
    python debug_job_detail.py
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE = Path(__file__).parent.parent / "browser-profile"
JOB_URL = "https://www.linkedin.com/jobs/view/REPLACE_WITH_JOB_ID/"

LOCATION_SELECTORS = [
    ".jobs-unified-top-card__bullet",
    ".job-details-jobs-unified-top-card__primary-description-without-tagline",
    ".job-details-jobs-unified-top-card__primary-description",
    ".jobs-unified-top-card__primary-description",
    ".tvm__text",
    ".job-details-jobs-unified-top-card__subtitle-primary-grouping",
    ".job-details-jobs-unified-top-card__job-insight",
    "span.tvm__text--positive",
    "[class*='location']",
    "[class*='Location']",
    "[class*='primary-description']",
    "[class*='bullet']",
    "[class*='subtitle']",
]

WORK_TYPE_SELECTORS = [
    ".jobs-unified-top-card__workplace-type",
    ".job-details-jobs-unified-top-card__workplace-type",
    ".job-details-jobs-unified-top-card__remote-work-type",
    "[class*='workplace']",
    "[class*='workplaceType']",
    "[class*='work-type']",
    "[class*='remote']",
]


async def probe(page, selectors: list, label: str):
    print(f"\n── {label} ──")
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            for el in els[:3]:
                txt = (await el.inner_text()).strip()
                cls = await el.get_attribute("class") or ""
                if txt:
                    print(f"  [{sel}] → '{txt[:80]}' (class='{cls[:60]}')")
        except Exception as e:
            pass  # selector syntax errors etc.


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=False,
            args=["--start-maximized"],
        )
        page = await ctx.new_page()
        print(f"Loading: {JOB_URL}")
        await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        await probe(page, LOCATION_SELECTORS, "LOCATION SELECTORS")
        await probe(page, WORK_TYPE_SELECTORS, "WORK TYPE SELECTORS")

        # Broader scan — dump all top-card class names
        print("\n── top-card element classes ──")
        classes = await page.evaluate("""
            () => {
                const results = [];
                const els = document.querySelectorAll(
                    '[class*="top-card"], [class*="primary-description"], [class*="workplace"], [class*="location"]'
                );
                for (const el of els) {
                    const txt = (el.innerText || '').trim().slice(0, 80);
                    if (txt) results.push({cls: el.className.slice(0, 100), txt});
                }
                return results.slice(0, 30);
            }
        """)
        for item in classes:
            print(f"  .{item['cls'][:80]}\n    → '{item['txt']}'")

        # Scan for "Remote", "Hybrid", "On-site" text in the page header area
        print("\n── work-type text scan ──")
        wt_found = await page.evaluate("""
            () => {
                const keywords = ['Remote', 'Hybrid', 'On-site', 'Onsite'];
                const results = [];
                for (const el of document.querySelectorAll('*')) {
                    const txt = (el.childNodes.length === 1 && el.firstChild.nodeType === 3)
                        ? el.firstChild.textContent.trim()
                        : '';
                    if (keywords.some(k => txt.includes(k)) && txt.length < 40) {
                        results.push({tag: el.tagName, cls: el.className.slice(0, 80), txt});
                    }
                }
                return results.slice(0, 20);
            }
        """)
        for item in wt_found:
            print(f"  <{item['tag']} class='{item['cls']}'> → '{item['txt']}'")

        await ctx.close()
        print("\n── Debug complete ──")


if __name__ == "__main__":
    asyncio.run(main())
