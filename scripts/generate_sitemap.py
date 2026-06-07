#!/usr/bin/env python3
"""Generate sitemap.xml (sitemapindex) + sitemap-pages.xml + robots.txt."""
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
BASE_URL = "https://worlddishatlas.com"


def collect() -> list[str]:
    urls = []
    for f in sorted(CONTENT.rglob("index.html")):
        rel = f.parent.relative_to(CONTENT).as_posix()
        if rel == ".":
            urls.append(f"{BASE_URL}/")
        else:
            urls.append(f"{BASE_URL}/{rel}/")
    return urls


def write_sitemap_pages(urls):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        priority = "0.8"
        changefreq = "weekly"
        if u == f"{BASE_URL}/" or u.endswith("/dish/") or u.endswith("/cuisine/"):
            priority = "1.0"
            changefreq = "daily"
        elif "/dish/" in u:
            priority = "0.9"
        lines.append(
            f"  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority></url>"
        )
    lines.append("</urlset>")
    (CONTENT / "sitemap-pages.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote content/sitemap-pages.xml ({len(urls)} URLs)")


def write_sitemap_index():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <sitemap><loc>{BASE_URL}/sitemap-pages.xml</loc><lastmod>{today}</lastmod></sitemap>",
        f"  <sitemap><loc>{BASE_URL}/sitemap-images.xml</loc><lastmod>{today}</lastmod></sitemap>",
        "</sitemapindex>",
    ]
    (CONTENT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote content/sitemap.xml (sitemapindex)")


def write_robots():
    text = """User-agent: *
Allow: /

# AI training / retrieval bots welcome
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
    (CONTENT / "robots.txt").write_text(text, encoding="utf-8")
    print(f"  wrote content/robots.txt")


def main():
    urls = collect()
    if not urls:
        print("No URLs", file=sys.stderr); return 1
    write_sitemap_pages(urls)
    write_sitemap_index()
    write_robots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
