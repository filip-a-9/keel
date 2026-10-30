#!/usr/bin/env python3
"""Tell IndexNow search engines (Bing, Yandex and others) about every URL in
docs/sitemap.xml. Stdlib only. No account needed: the key file is served at
<BASE_URL><key>.txt (written by build.py).

Run ONLY after the site is deployed and the key file is live:
    python3 tools/indexnow.py          # dry run: prints the request
    python3 tools/indexnow.py --send   # sends it
"""
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

key = (ROOT / "src/indexnow-key.txt").read_text(encoding="utf-8").strip()
urls = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "docs/sitemap.xml").read_text())
host = urlparse(build.BASE_URL).netloc
payload = {
    "host": host,
    "key": key,
    # keyLocation must sit under the URLs' path (/keel/), which it does
    "keyLocation": f"{build.BASE_URL}{key}.txt",
    "urlList": urls,
}
print(json.dumps(payload, indent=2))
if "--send" not in sys.argv:
    print("\nDry run. Add --send after the push to submit.")
    sys.exit(0)
req = urllib.request.Request(
    "https://api.indexnow.org/indexnow",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json; charset=utf-8"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as r:
    print("HTTP", r.status)
