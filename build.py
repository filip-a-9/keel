#!/usr/bin/env python3
"""Build the static site from src/ into docs/. Python standard library only.

Run: python3 build.py
The canonical base URL lives in BASE_URL below and nowhere else. To move to a
custom domain, change that one line and rebuild.
"""

import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

BASE_URL = "https://filip-a-9.github.io/keel/"  # the one place to change
SITE_NAME = "Keel AI Visibility"
EMAIL = "keel.agents@gmail.com"
PUBLISHED = "2026-10-30"

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "docs"

NAV = [
    ("/offer/", "Offer"),
    ("/method/", "Method"),
    ("/case-study/", "Case study"),
    ("/articles/", "Articles"),
    ("/faq/", "FAQ"),
    ("/order/", "Order"),
]
FOOT = NAV + [("/sample-report/", "Sample report"), ("/terms/", "Terms"), ("/privacy/", "Privacy")]

TIERS = [
    {
        "name": "Snapshot",
        "price": "249",
        "desc": "AI visibility audit of ChatGPT answers: 6 question themes, "
        "delivered as an HTML and PDF report by email in 5 working days.",
    },
    {
        "name": "Full",
        "price": "749",
        "desc": "AI visibility audit of ChatGPT and Claude answers: 10 to 15 question "
        "themes, with findings and recommended actions, delivered as an HTML and "
        "PDF report by email in 7 working days.",
    },
]


def abs_url(path: str) -> str:
    return BASE_URL + path.lstrip("/")


def rel(from_dir: str, to_path: str) -> str:
    """Relative URL from a page in `from_dir` (e.g. 'articles/x') to a site path."""
    depth = len([p for p in from_dir.split("/") if p])
    target = to_path.lstrip("/")
    return ("../" * depth + target) or "./"


def rewrite_links(body: str, page_dir: str, absolute: bool) -> str:
    def sub(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith("//"):
            return m.group(0)
        new = abs_url(url) if absolute else rel(page_dir, url)
        return f'{attr}="{new}"'

    return re.sub(r'(href|src)="(/[^"]*)"', sub, body)


def parse(path: Path):
    head, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, body.strip()


def jsonld(obj) -> str:
    data = json.dumps(obj, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{data}\n</script>'


def provider():
    return {
        "@type": "ProfessionalService",
        "@id": abs_url("/#service"),
        "name": SITE_NAME,
        "url": abs_url("/"),
        "logo": abs_url("/assets/logo.svg"),
        "image": abs_url("/assets/og-image.png"),
        "email": EMAIL,
        "description": "Independent AI visibility audits: how often ChatGPT and "
        "Claude mention a brand, with 95% confidence intervals, cited pages and "
        "recommended actions. An independent, brand-only service.",
        "areaServed": {"@type": "Country", "name": "United Kingdom"},
        "priceRange": "GBP 249 - GBP 749",
        "knowsLanguage": "en-GB",
    }


def offers():
    out = []
    for t in TIERS:
        out.append(
            {
                "@type": "Offer",
                "name": f"{t['name']} AI visibility audit",
                "description": t["desc"],
                "price": t["price"],
                "priceCurrency": "GBP",
                "url": abs_url("/offer/"),
                "availability": "https://schema.org/InStock",
                "seller": {"@id": abs_url("/#service")},
                "itemOffered": {
                    "@type": "Service",
                    "name": f"{t['name']} AI visibility audit",
                    "provider": {"@id": abs_url("/#service")},
                },
            }
        )
    return out


def website():
    return {
        "@type": "WebSite",
        "@id": abs_url("/#website"),
        "name": SITE_NAME,
        "url": abs_url("/"),
        "inLanguage": "en-GB",
        "publisher": {"@id": abs_url("/#service")},
    }


def faq_html(items):
    parts = []
    for it in items:
        parts.append(
            f"<details><summary>{html.escape(it['q'])}</summary>"
            f"<p>{it['a_html']}</p></details>"
        )
    # No FAQPage JSON-LD: Google restricts FAQ rich results. Plain HTML only.
    return "\n".join(parts)


def layout(*, title, desc, path, body, ld, kind="website", absolute=False,
           noindex=False, article_meta=None):
    page_dir = path.strip("/")
    full_title = title
    canon = abs_url(path)

    def link(p):
        return abs_url(p) if absolute else rel(page_dir, p)

    nav = "".join(
        f'<li><a href="{link(u)}"'
        + (' aria-current="page"' if u == path else "")
        + f">{n}</a></li>"
        for u, n in NAV
    )
    foot = "".join(f'<li><a href="{link(u)}">{n}</a></li>' for u, n in FOOT)
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    og_type = "article" if kind == "article" else "website"
    ld_html = "\n".join(jsonld(x) for x in ld)
    body = rewrite_links(body, page_dir, absolute)
    css = link("/assets/style.css")
    cta = "" if path == "/order/" else (
        '<aside class="cta" aria-label="Order"><div class="wrap">'
        "<p><strong>Founding price for the first 3 customers: Snapshot £149 "
        "(list £249) and Full £449 (list £749).</strong> In exchange, you give "
        "permission to publish an anonymised case study.</p>"
        f'<a class="btn" href="{link("/order/")}">Order a Snapshot (£249)</a>'
        "</div></aside>"
    )
    OG_IMAGE = abs_url("/assets/og-image.png")
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
{robots}<link rel="canonical" href="{canon}">
<meta name="color-scheme" content="light">
<link rel="icon" href="{link('/assets/favicon.svg')}" type="image/svg+xml">
<link rel="preload" href="{link('/assets/fonts/fraunces-latin-600-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="en_GB">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{html.escape(full_title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Keel AI Visibility: does ChatGPT recommend your brand? Measured, not guessed.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(full_title, quote=True)}">
<meta name="twitter:description" content="{html.escape(desc, quote=True)}">
<meta name="twitter:image" content="{OG_IMAGE}">
{ld_html}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
<a class="brand" href="{link('/')}"><img src="{link('/assets/logo.svg')}" width="26" height="26" alt=""><span>{SITE_NAME}</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
{cta}
<footer class="site"><div class="wrap">
<nav aria-label="Footer"><ul>{foot}</ul></nav>
<p>Keel AI Visibility is an independent service. Contact: <a href="mailto:{EMAIL}">{EMAIL}</a>. No cookies, no tracking, no analytics.</p>
<p>Independent. Not affiliated with OpenAI, Anthropic or any brand named on this site.</p>
</div></footer>
</body>
</html>
"""


def write(path: str, text: str):
    p = OUT / path.strip("/") / "index.html" if path != "/404" else OUT / "404.html"
    if path == "/":
        p = OUT / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


SAMPLE_TITLE = "Sample AI visibility report: Teamwork.com | Keel AI"
SAMPLE_DESC = (
    "The full report from Keel's independent Teamwork.com study: 280 ChatGPT "
    "answers, mention rates with 95% intervals, cited pages, the method and its limits."
)


def sample_report() -> str:
    """Wrap the real report (src/sample-report/report.html) with site metadata and
    a banner. The report is a self-contained document; its own styles are kept."""
    path = "/sample-report/"
    t = (SRC / "sample-report" / "report.html").read_text(encoding="utf-8")
    canon = abs_url(path)
    og = abs_url("/assets/og-image.png")
    e = lambda s: html.escape(s, quote=True)  # noqa: E731
    head = (
        f"<title>{e(SAMPLE_TITLE)}</title>\n"
        f'<meta name="description" content="{e(SAMPLE_DESC)}">\n'
        '<meta name="color-scheme" content="light">\n'
        f'<link rel="canonical" href="{canon}">\n'
        f'<link rel="icon" href="{abs_url("/assets/favicon.svg")}" type="image/svg+xml">\n'
        f'<meta property="og:site_name" content="{SITE_NAME}">\n'
        '<meta property="og:locale" content="en_GB">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{e(SAMPLE_TITLE)}">\n'
        f'<meta property="og:description" content="{e(SAMPLE_DESC)}">\n'
        f'<meta property="og:url" content="{canon}">\n'
        f'<meta property="og:image" content="{og}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta property="og:image:alt" content="Keel AI Visibility sample report">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{e(SAMPLE_TITLE)}">\n'
        f'<meta name="twitter:description" content="{e(SAMPLE_DESC)}">\n'
        f'<meta name="twitter:image" content="{og}">\n'
    )
    t, n = re.subn(r"<title>.*?</title>", lambda m: head, t, count=1, flags=re.S)
    assert n == 1
    t = t.replace('<html lang="en">', '<html lang="en-GB">', 1)
    banner = (
        '<div style="max-width:900px;margin:0 auto 16px;padding:12px 16px;'
        "background:#eef6f4;border-left:4px solid #1b6e63;color:#0f2742;"
        'font:15px/1.5 system-ui,sans-serif">'
        "<strong>Sample: independent study, not commissioned by or affiliated "
        "with Teamwork.com.</strong> This is the report format Keel delivers. "
        f'<a href="{rel(path.strip("/"), "/case-study/")}" style="color:#1b6e63">Case study summary</a> &nbsp; '
        f'<a href="{rel(path.strip("/"), "/offer/")}" style="color:#1b6e63">Offer</a> &nbsp; '
        f'<a href="{rel(path.strip("/"), "/order/")}" style="color:#1b6e63">Order a Snapshot (£249)</a>'
        "</div>\n"
    )
    t = t.replace("<body>", "<body>\n" + banner, 1)
    write(path, t)
    return path


def main():
    # clean everything except .nojekyll
    for child in OUT.iterdir():
        if child.name == ".nojekyll":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    (OUT / ".nojekyll").touch()
    shutil.copytree(SRC / "assets", OUT / "assets")
    # IndexNow key file: docs/<key>.txt containing the key
    key = (SRC / "indexnow-key.txt").read_text(encoding="utf-8").strip()
    (OUT / f"{key}.txt").write_text(key, encoding="utf-8")
    # Search Console verification files (google*.html), copied unchanged
    for g in SRC.glob("google*.html"):
        shutil.copyfile(g, OUT / g.name)

    questionnaire = (SRC / "questionnaire.txt").read_text(encoding="utf-8").strip()
    mailto = (
        f"mailto:{EMAIL}?subject="
        + urllib.parse.quote("Keel AI Visibility order")
        + "&body="
        + urllib.parse.quote(questionnaire.split("\n", 2)[2].strip())
    )
    faq_items = json.loads((SRC / "faq.json").read_text(encoding="utf-8"))
    faq_body = faq_html(faq_items)

    articles = []
    for f in sorted((SRC / "articles").glob("*.html")):
        meta, body = parse(f)
        meta["slug"] = f.stem
        meta["body"] = body
        articles.append(meta)
    articles.sort(key=lambda m: int(m.get("order", 99)))

    art_list = "<ul class=\"articles\">" + "".join(
        f'<li><h2><a href="/articles/{a["slug"]}/">{html.escape(a["h1"])}</a></h2>'
        f'<p>{html.escape(a["description"])}</p></li>'
        for a in articles
    ) + "</ul>"

    public = []  # (path, lastmod)
    ctx = {
        "{{faq}}": faq_body,
        "{{article_list}}": art_list,
        "{{questionnaire}}": html.escape(questionnaire),
        "{{mailto}}": html.escape(mailto, quote=True),
        "{{email}}": EMAIL,
        "{{figure}}": (SRC / "figure.svg").read_text(encoding="utf-8").strip(),
    }

    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse(f)
        for k, v in ctx.items():
            body = body.replace(k, v)
        stem = f.stem
        if stem == "404":
            path = "/404"
            text = layout(
                title=meta["title"], desc=meta["description"], path="/404.html",
                body=body, ld=[], absolute=True, noindex=True,
            )
            write("/404", text)
            continue
        path = "/" if stem == "index" else f"/{stem}/"
        ld = []
        if stem == "index":
            ld = [{"@context": "https://schema.org", **provider()}]
            ld[0]["hasOfferCatalog"] = {
                "@type": "OfferCatalog",
                "name": "AI visibility audits",
                "itemListElement": offers(),
            }
            ld.append({"@context": "https://schema.org", **website()})
        elif stem == "offer":
            ld = [
                {"@context": "https://schema.org", **provider()},
                {"@context": "https://schema.org", **offers()[0]},
                {"@context": "https://schema.org", **offers()[1]},
            ]
        write(path, layout(title=meta["title"], desc=meta["description"],
                           path=path, body=body, ld=ld))
        public.append(path)

    for a in articles:
        path = f"/articles/{a['slug']}/"
        art_ld = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": a["h1"],
            "description": a["description"],
            "datePublished": a.get("published", PUBLISHED),
            "dateModified": a.get("published", PUBLISHED),
            "inLanguage": "en-GB",
            "mainEntityOfPage": abs_url(path),
            "author": {"@type": "Organization", "name": SITE_NAME, "url": abs_url("/")},
            "publisher": {"@type": "Organization", "name": SITE_NAME, "url": abs_url("/")},
        }
        others = [b for b in articles if b is not a][:3]
        related = "".join(
            f'<li><a href="/articles/{b["slug"]}/">{html.escape(b["h1"])}</a></li>'
            for b in others
        )
        body = (
            f'<article>\n<h1>{html.escape(a["h1"])}</h1>\n'
            f'<p class="meta">Published {a.get("published", PUBLISHED)} by {SITE_NAME}. '
            f"{a.get('reading', '')}</p>\n{a['body']}\n"
            '<aside class="related"><h2>Keep reading</h2><ul>' + related + "</ul>"
            '<p><a class="btn" href="/offer/">See the audit offer</a></p></aside>\n'
            "</article>"
        )
        write(path, layout(title=a["title"], desc=a["description"], path=path,
                           body=body, ld=[art_ld], kind="article"))
        public.append(path)

    public.append(sample_report())
    public.append("/articles/")  # generated from pages/articles.html if present
    # sitemap
    urls = sorted(set(public), key=lambda p: (p != "/", p))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in urls:
        prio = "<priority>1.0</priority>" if p == "/" else ""
        sm.append(
            f"<url><loc>{abs_url(p)}</loc><lastmod>{PUBLISHED}</lastmod>{prio}</url>"
        )
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {abs_url('/sitemap.xml')}\n",
        encoding="utf-8",
    )
    print(f"built {len(urls)} public pages -> {OUT}")


if __name__ == "__main__":
    main()
