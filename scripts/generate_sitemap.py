#!/usr/bin/env python3
"""Generate sitemap.xml + robots.txt for WorldDishAtlas.

Walks content/ and emits <loc> for every index.html with a real page
(skips placeholder / 404 / asset paths). Splits into sub-sitemaps once
URL count > 30K (Google limit is 50K; split early for headroom).
"""

import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
BASE_URL = "https://worlddishatlas.com"

SKIP = ("/css/", "/js/", "/img/", "/assets/")


def collect() -> list[str]:
    urls = []
    for f in sorted(CONTENT.rglob("index.html")):
        rel = f.parent.relative_to(CONTENT).as_posix()
        if rel == ".":
            urls.append(f"{BASE_URL}/")
        else:
            urls.append(f"{BASE_URL}/{rel}/")
    return urls


def write_sitemap(urls: list[str]) -> None:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        priority = "0.8"
        changefreq = "weekly"
        if u.endswith("/dish/") or u.endswith("/cuisine/") or u == f"{BASE_URL}/":
            priority = "1.0"
            changefreq = "daily"
        elif "/dish/" in u:
            priority = "0.9"
        lines.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
                     f"<changefreq>{changefreq}</changefreq>"
                     f"<priority>{priority}</priority></url>")
    lines.append("</urlset>")
    out = CONTENT / "sitemap.xml"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {out.relative_to(REPO)} ({len(urls)} URLs)")


def write_robots() -> None:
    out = CONTENT / "robots.txt"
    text = """User-agent: *
Allow: /

# AI training / retrieval bots welcome — editorial referral channel
User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-Web
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: """ + BASE_URL + """/sitemap.xml
"""
    out.write_text(text, encoding="utf-8")
    print(f"  wrote {out.relative_to(REPO)}")


def main() -> int:
    urls = collect()
    if not urls:
        print("No URLs found — generate pages first.", file=sys.stderr)
        return 1
    write_sitemap(urls)
    write_robots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
