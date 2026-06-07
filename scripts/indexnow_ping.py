#!/usr/bin/env python3
"""IndexNow ping: notify Bing + Yandex when content changes. Free,
instant, no auth beyond hosting a key file at /key.txt.

Setup: drop a 16-char alphanumeric key at content/<KEY>.txt, then
this script pings IndexNow with the changed URLs.

Usage:
    python3 scripts/indexnow_ping.py                  # ping every URL on the site
    python3 scripts/indexnow_ping.py --dish carbonara # ping one dish
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
BASE = "https://worlddishatlas.com"


def find_key():
    """Find the 16+ char IndexNow key file in content/."""
    key = os.environ.get("WDA_INDEXNOW_KEY")
    if key:
        return key
    for f in CONTENT.glob("*.txt"):
        if len(f.stem) >= 16 and f.stem.isalnum() and f.stem.lower() == f.stem:
            return f.stem
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dish", help="Ping one dish URL")
    p.add_argument("--all", action="store_true", help="Ping every URL from the sitemap")
    args = p.parse_args()

    key = find_key()
    if not key:
        print("No IndexNow key found. Set WDA_INDEXNOW_KEY env var "
              "OR drop <key>.txt (≥16 alphanumeric chars) into content/.",
              file=sys.stderr)
        return 2

    if args.dish:
        urls = [f"{BASE}/dish/{args.dish}/"]
    elif args.all:
        # Read from sitemap-pages.xml
        import re
        sm = CONTENT / "sitemap-pages.xml"
        if not sm.exists():
            print("No sitemap-pages.xml; run generate_sitemap.py first", file=sys.stderr)
            return 2
        urls = re.findall(r"<loc>([^<]+)</loc>", sm.read_text())
    else:
        print("Pass --dish <slug> or --all", file=sys.stderr)
        return 2

    payload = {
        "host": "worlddishatlas.com",
        "key": key,
        "keyLocation": f"{BASE}/{key}.txt",
        "urlList": urls,
    }

    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        print(f"IndexNow ping: HTTP {r.status} for {len(urls)} URL(s)")
        return 0
    except urllib.error.HTTPError as e:
        print(f"IndexNow ping failed: HTTP {e.code} {e.reason}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"IndexNow ping error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
