#!/usr/bin/env python3
"""Render src/assets/og-image.png (1200x630) from tools/og.html + src/figure.svg.
Needs Playwright (isolated in .venv): .venv/bin/python tools/make_og.py"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

html = (ROOT / "tools/og.html").read_text(encoding="utf-8").replace(
    "FIGURE", (ROOT / "src/figure.svg").read_text(encoding="utf-8")
).replace("filip-a-9.github.io/keel", build.BASE_URL.split("//")[1].rstrip("/"))
tmp = ROOT / "tools/_og_render.html"
tmp.write_text(html, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto(tmp.as_uri())
    pg.screenshot(path=str(ROOT / "src/assets/og-image.png"))
    b.close()
tmp.unlink()
print("wrote src/assets/og-image.png")
