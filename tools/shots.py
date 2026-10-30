#!/usr/bin/env python3
"""Full-page screenshots of the built site at 1280 and 390 px.
Run: .venv/bin/python tools/shots.py (Playwright lives in the isolated .venv)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "home": "docs/index.html",
    "case-study": "docs/case-study/index.html",
    "article": "docs/articles/why-one-chatgpt-screenshot-proves-nothing/index.html",
    "offer": "docs/offer/index.html",
    "sample-report": "docs/sample-report/index.html",
}
out = ROOT / "marketing/screenshots"
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for w in (1280, 390):
        pg = b.new_page(viewport={"width": w, "height": 900})
        for name, rel in PAGES.items():
            pg.goto((ROOT / rel).as_uri())
            pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(1300)
            pg.screenshot(path=str(out / f"{name}-{w}.png"), full_page=True)
            over = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            print(name, w, "horizontal overflow px:", over)
    b.close()
