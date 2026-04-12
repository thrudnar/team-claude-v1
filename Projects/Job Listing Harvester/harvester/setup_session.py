"""
setup_session.py — One-time LinkedIn login for Argus
Run this once to create a persistent browser profile with your LinkedIn session.
After running, close the browser window and the session will be saved.

Usage:
    python setup_session.py
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path(__file__).parent.parent / "browser-profile"

async def main():
    PROFILE_DIR.mkdir(exist_ok=True)
    print(f"Opening browser with persistent profile at: {PROFILE_DIR}")
    print("Log into LinkedIn, then close the browser window.")
    print("Your session will be saved for future harvests.\n")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=["--start-maximized"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("Browser open. Log in and close the window when done.")
        # Wait for user to close the browser
        await ctx.wait_for_event("close", timeout=0)

    print("\nSession saved. You can now run harvest.py.")

if __name__ == "__main__":
    asyncio.run(main())
