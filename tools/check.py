#!/usr/bin/env python3
"""Check docs/: internal links and anchors resolve, JSON-LD parses, sitemap is
complete. Stdlib only. Run: python3 tools/check.py (after python3 build.py)."""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

BASE = build.BASE_URL


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.ld, self._ld = [], set(), [], False
        self.imgs_noalt, self.h1 = [], 0
        self.title = self.desc = self.canon = None
        self.heads, self.meta = [], {}
        self._t = False
        self._inbody = False

    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if k in a and a[k]:
                self.links.append(a[k])
        if tag == "img" and "alt" not in a:
            self.imgs_noalt.append(a.get("src"))
        if tag == "h1":
            self.h1 += 1
        if tag in ("h1", "h2", "h3", "h4"):
            self.heads.append(int(tag[1]))
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k:
                self.meta[k] = a.get("content")
        if tag == "meta" and a.get("name") == "viewport":
            self.meta["viewport"] = "1"
        if tag == "body":
            self._inbody = True
        if tag == "title" and not self._inbody:
            self._t = True
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content")
        if tag == "link" and a.get("rel") == "canonical":
            self.canon = a.get("href")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = True
            self.ld.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._ld = False
        if tag == "title":
            self._t = False

    def handle_data(self, d):
        if self._ld:
            self.ld[-1] += d
        if self._t:
            self.title = (self.title or "") + d


def resolve(page: Path, url: str):
    """Return (file path or None) for an internal URL, else 'external'."""
    if url.startswith(("mailto:", "tel:")):
        return "external"
    full = urljoin(BASE + page.relative_to(DOCS).as_posix(), url)
    if not full.startswith(BASE):
        return "external"
    path = unquote(urlparse(full).path)[len(urlparse(BASE).path):]
    f = DOCS / path
    if f.is_dir() or path == "" or path.endswith("/"):
        f = f / "index.html"
    return f


errors, titles, descs = [], {}, {}
# google*.html are Search Console verification files, not site pages
pages = sorted(p for p in DOCS.rglob("*.html") if not p.name.startswith("google"))
parsed = {}
for page in pages:
    p = P()
    p.feed(page.read_text(encoding="utf-8"))
    parsed[page] = p
for page, p in parsed.items():
    name = page.relative_to(DOCS).as_posix()
    if p.h1 != 1:
        errors.append(f"{name}: {p.h1} h1 elements")
    for src in p.imgs_noalt:
        errors.append(f"{name}: img without alt {src}")
    if not p.title or not p.desc:
        errors.append(f"{name}: missing title/description")
    if name != "404.html":
        if not 50 <= len(p.title or "") <= 60:
            errors.append(f"{name}: title length {len(p.title or '')} (want 50-60)")
        if not 150 <= len(p.desc or "") <= 160:
            errors.append(f"{name}: description length {len(p.desc or '')} (want 150-160)")
    for k in ("og:title", "og:description", "og:image", "og:image:width",
              "og:image:height", "og:url", "og:type", "og:site_name",
              "twitter:card", "twitter:title", "twitter:description",
              "twitter:image", "viewport"):
        if not p.meta.get(k):
            errors.append(f"{name}: missing {k}")
    if p.meta.get("twitter:card") != "summary_large_image":
        errors.append(f"{name}: twitter:card not summary_large_image")
    for prev, cur in zip(p.heads, p.heads[1:]):
        if cur > prev + 1:
            errors.append(f"{name}: heading level skipped (h{prev} to h{cur})")
    for raw in p.ld:
        if '"FAQPage"' in raw or '"Person"' in raw:
            errors.append(f"{name}: FAQPage/Person JSON-LD present")
    titles.setdefault(p.title, []).append(name)
    descs.setdefault(p.desc, []).append(name)
    for i, raw in enumerate(p.ld):
        try:
            json.loads(raw)
        except Exception as e:
            errors.append(f"{name}: JSON-LD block {i} invalid: {e}")
    for url in p.links:
        r = resolve(page, urldefrag(url)[0] or page.name) if urldefrag(url)[0] or not url.startswith("#") else page
        if r == "external":
            if url.startswith("http") and not url.startswith(BASE):
                pass
            continue
        if not r.exists():
            errors.append(f"{name}: broken link {url} -> {r}")
            continue
        frag = urldefrag(url)[1]
        if frag and r.suffix == ".html" and r in parsed and frag not in parsed[r].ids:
            errors.append(f"{name}: missing anchor {url}")
for d, names in (*titles.items(), *descs.items()):
    if len(names) > 1:
        errors.append(f"duplicate title/description {d!r}: {names}")

# sitemap vs pages
sm = (DOCS / "sitemap.xml").read_text()
locs = set(re.findall(r"<loc>([^<]+)</loc>", sm))
expected = set()
for page in pages:
    rel = page.relative_to(DOCS).as_posix()
    if rel == "404.html":
        continue
    expected.add(BASE + ("" if rel == "index.html" else rel[: -len("index.html")]))
for m in expected - locs:
    errors.append(f"sitemap missing {m}")
for m in locs - expected:
    errors.append(f"sitemap has non-page {m}")
for page in pages:
    p = parsed[page]
    rel = page.relative_to(DOCS).as_posix()
    if rel != "404.html" and p.canon not in expected:
        errors.append(f"{rel}: canonical {p.canon} not in expected URLs")
og = (DOCS / "assets/og-image.png").read_bytes()
if og[:8] != b"\x89PNG\r\n\x1a\n" or int.from_bytes(og[16:20], "big") != 1200 or int.from_bytes(og[20:24], "big") != 630:
    errors.append("og-image.png is not a 1200x630 PNG")
for must in ("robots.txt", ".nojekyll", "404.html"):
    if not (DOCS / must).exists():
        errors.append(f"missing docs/{must}")
if "marketing" in sm:
    errors.append("sitemap mentions marketing")
if (DOCS / "marketing").exists():
    errors.append("marketing in docs/")

n_ld = sum(len(p.ld) for p in parsed.values())
links = sum(len(p.links) for p in parsed.values())
print(f"pages={len(pages)} links_checked={links} jsonld_blocks={n_ld} sitemap_urls={len(locs)}")
print("OK" if not errors else "\n".join(errors))
sys.exit(1 if errors else 0)
