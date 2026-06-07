#!/usr/bin/env python3
"""HEAD-check every dish's verified URLs + confirm the page mentions
the dish name. Mirrors TableJourney's verify_entities.py pattern.

Exit 1 on any HARD failure. Anti-bot 401/403/429 are WARN, not HARD.
"""
import argparse
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DISHES = REPO / "site-data" / "dishes"

UA = "Mozilla/5.0 (compatible; WDA-Validator/1.0)"
TIMEOUT = 8
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def head_check(url: str) -> tuple[int, str]:
    """Return (status_code, body_text or '')."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, context=ctx, timeout=TIMEOUT)
        return r.status, ""
    except urllib.error.HTTPError as e:
        if e.code in (405,):  # method-not-allowed → try GET
            return get_check(url)
        return e.code, ""
    except Exception:
        return get_check(url)


def get_check(url: str) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, context=ctx, timeout=TIMEOUT)
        body = r.read(50_000).decode("utf-8", errors="replace")
        return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


def check_dish(slug: str, d: dict, issues: list, deep: bool) -> None:
    v = d.get("verified", {})
    if not v:
        issues.append(("HARD", f"{slug}: no verified block"))
        return
    for field in ("source_url", "history_evidence_url"):
        url = v.get(field)
        if not url:
            issues.append(("HARD", f"{slug}: missing verified.{field}"))
            continue
        status, body = head_check(url)
        if status == 0:
            issues.append(("HARD", f"{slug}: {field} unreachable: {url}"))
        elif status in (401, 403, 429):
            issues.append(("WARN", f"{slug}: {field} returned {status} (likely anti-bot, accepting): {url}"))
        elif status >= 400:
            issues.append(("HARD", f"{slug}: {field} returned {status}: {url}"))
        elif deep and field == "source_url" and body:
            # Confirm dish name (or alias) appears in the page text
            text = re.sub(r"<[^>]+>", " ", body).lower()
            name = d.get("name", "").lower()
            native = d.get("name_native", "").lower()
            if name and name not in text and (not native or native not in text):
                issues.append(("WARN", f"{slug}: source_url page does not mention '{d.get('name')}' — verify the source actually describes this dish"))
        time.sleep(0.3)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dish", help="One slug")
    p.add_argument("--deep", action="store_true",
                   help="Also fetch source_url page + verify dish name appears")
    args = p.parse_args()

    files = ([DISHES / f"{args.dish}.json"] if args.dish
             else sorted(DISHES.glob("*.json")))

    issues = []
    for fp in files:
        if not fp.exists():
            print(f"ERR: missing {fp}", file=sys.stderr)
            return 2
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(("HARD", f"{fp.stem}: parse error: {e}"))
            continue
        check_dish(fp.stem, d, issues, deep=args.deep)

    for lvl, msg in issues:
        print(f"   {lvl}: {msg}")
    hard = sum(1 for lvl, _ in issues if lvl == "HARD")
    warn = sum(1 for lvl, _ in issues if lvl == "WARN")
    print(f"\nVerified {len(files)} dish(es). HARD: {hard}  WARN: {warn}")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
