"""
inspect_scroll.py — Diagnostic tool for investigating LinkedIn page structure.

## History
Built during v2 pagination work (2026-04-02) to determine why the harvester
was only capturing 25 jobs per collection (page 1 only). Key findings:

- LinkedIn collections use PAGINATION (Next button), not infinite scroll.
  The button selector is: button.artdeco-button--icon-right
  Clicking it replaces the current 25 job cards with the next 25.

- LinkedIn uses obfuscated CSS class names (e.g. MOxXkDGHFAubGcoMVTSaBoubxekMIrAo)
  for the job list container — these change across deploys and cannot be
  hardcoded. Anchor on data attributes instead (data-results-list-top-scroll-sentinel).

- window.scrollTo() and page.mouse.wheel() do NOT trigger additional job loads.
  The job list container's scrollTop stays at 0 regardless. Pagination is the
  only mechanism.

- The two scrollable containers on the page are:
    1. The job list panel (obfuscated class, scrollH ~3500, clientH ~571)
    2. The job detail panel (jobs-search__job-details--wrapper)

## When to use this tool
- Before implementing a new source (Jobright, BuiltIn) to understand its
  DOM structure and pagination mechanism before writing scraper code.
- When the harvester stops picking up jobs (LinkedIn may change selectors
  or switch from pagination to infinite scroll or vice versa).
- When debugging why scroll/pagination logic isn't working headlessly.

Usage:
    python inspect_scroll.py
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE    = Path(__file__).parent
PROFILE = BASE.parent / "browser-profile"
URL     = "https://www.linkedin.com/jobs/collections/top-applicant/"


async def run():
    if not PROFILE.exists():
        print("No browser profile found. Run setup_session.py first.")
        sys.exit(1)

    print("Launching headed browser...")
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

        # Report how many job IDs are visible right now
        job_ids = await page.evaluate("""
            () => [...document.querySelectorAll('[data-occludable-job-id]')]
                .map(el => el.getAttribute('data-occludable-job-id'))
                .filter(Boolean)
        """)
        print(f"\nJob IDs visible in DOM right now: {len(job_ids)}")

        # Dump any elements that look scrollable
        scrollables = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    const overflow = style.overflow + style.overflowY;
                    if ((overflow.includes('auto') || overflow.includes('scroll'))
                        && el.scrollHeight > el.clientHeight + 10) {
                        results.push({
                            tag: el.tagName,
                            id: el.id || '',
                            classes: el.className.toString().slice(0, 120),
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight
                        });
                    }
                });
                return results;
            }
        """)

        print(f"\nScrollable elements found on page ({len(scrollables)} total):")
        for el in scrollables:
            print(f"  <{el['tag']}> id='{el['id']}' scrollH={el['scrollHeight']} clientH={el['clientHeight']}")
            if el['classes']:
                print(f"    classes: {el['classes']}")

        # Check for any "See more" / "Show more" / pagination buttons
        buttons = await page.evaluate("""
            () => {
                const btns = [];
                document.querySelectorAll('button, a').forEach(el => {
                    const t = (el.innerText || '').trim().toLowerCase();
                    if (t.includes('more') || t.includes('next') ||
                            t.includes('load') || t.includes('show')) {
                        btns.push({
                            tag: el.tagName,
                            text: el.innerText.trim().slice(0, 80),
                            classes: el.className.toString().slice(0, 80)
                        });
                    }
                });
                return btns;
            }
        """)
        print(f"\n'More/Next/Load' buttons found ({len(buttons)}):")
        for b in buttons:
            print(f"  <{b['tag']}> '{b['text']}' | classes: {b['classes']}")

        # Try mouse wheel scroll and check if count changes
        print("\nTrying mouse wheel scroll (3×)...")
        for i in range(3):
            await page.mouse.wheel(0, 1200)
            await asyncio.sleep(2.5)
            count = await page.evaluate("""
                () => [...new Set(
                    [...document.querySelectorAll('[data-occludable-job-id]')]
                    .map(el => el.getAttribute('data-occludable-job-id'))
                    .filter(Boolean)
                )].length
            """)
            print(f"  After wheel {i+1}: {count} job IDs in DOM")

        # Check if scrollable container's scrollTop changed
        scroll_info = await page.evaluate("""
            () => {
                const sentinel = document.querySelector('[data-results-list-top-scroll-sentinel]');
                if (!sentinel) return {found: false};
                let el = sentinel.parentElement;
                while (el && el !== document.body) {
                    const style = window.getComputedStyle(el);
                    const oy = style.overflowY;
                    if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) {
                        return {
                            found: true,
                            scrollTop: el.scrollTop,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            classes: el.className.toString().slice(0, 80)
                        };
                    }
                    el = el.parentElement;
                }
                return {found: false};
            }
        """)
        print(f"\nScroll container state: {scroll_info}")

        print("\n──────────────────────────────────────────────")
        print("Browser is open. Open DevTools (Cmd+Option+I) to inspect.")
        print("Try manually scrolling the job list and watch if new jobs appear.")
        print("\nPress Enter here to close the browser when done.")
        print("──────────────────────────────────────────────")

        input()
        await ctx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(run())
