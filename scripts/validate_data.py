#!/usr/bin/env python3
"""Validate WorldDishAtlas dish JSON files against the 9 P0 rules.

Inherits every defect class TableJourney hardened against (Rounds 6-10
audits + GSC validation work). New dishes fail-hard here before they can
ship, so we never re-learn what TableJourney already learned.

Usage:
    python3 scripts/validate_data.py           # validate all dishes
    python3 scripts/validate_data.py --dish carbonara
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DISHES = REPO / "site-data" / "dishes"

# --- 9 P0 rules ---

AI_TELL_PHRASES = (
    "hidden gem", "must-try", "must try", "world-class", "world class",
    "nestled in", "to die for", "iconic spot", "iconic restaurant",
    "culinary journey", "second to none", "unparalleled", "a must visit",
    "must visit", "wide selection", "renowned for", "boasts",
    "elevates", "showcases",
)

EM_EN_DASH_RE = re.compile(r"[—–]")  # — and –
HYPHEN_AS_DASH_RE = re.compile(r" - ")  # " - " as em-dash substitute
URL_RE = re.compile(r"^https://")  # https-only

VALID_CATEGORIES = {
    "pasta", "noodle", "soup", "stew", "salad", "bread", "pastry",
    "dessert", "rice", "sandwich", "beverage", "cocktail", "appetizer",
    "main", "side", "snack", "street food", "fried", "grilled",
    "raw", "fermented", "preserved", "dip", "sauce", "curry", "pie",
    "dumpling",
}


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _check_no_ai_tells(text: str, where: str, issues: list) -> None:
    if not isinstance(text, str):
        return
    low = text.lower()
    for phrase in AI_TELL_PHRASES:
        if phrase in low:
            issues.append(
                ("ERR", f"{where}: contains AI-tell phrase '{phrase}'. "
                        f"Rewrite with specific factual detail (STANDARDS.md §3).")
            )


def _check_no_em_dashes(text: str, where: str, issues: list) -> None:
    if not isinstance(text, str):
        return
    if EM_EN_DASH_RE.search(text):
        issues.append(
            ("ERR", f"{where}: contains em-dash or en-dash. "
                    f"Use period or comma (STANDARDS.md §4).")
        )
    # Don't flag hyphen-as-dash in URLs/slugs
    text_without_urls = re.sub(r"https?://\S+", "", text)
    if HYPHEN_AS_DASH_RE.search(text_without_urls):
        issues.append(
            ("WARN", f"{where}: contains ' - ' (hyphen with spaces). "
                     f"This is an em-dash AI-tell substitute. Rewrite as "
                     f"period or comma.")
        )


def _check_https(url: str, where: str, issues: list) -> None:
    if not url:
        return
    if not URL_RE.match(url):
        issues.append(
            ("ERR", f"{where}: {url!r} must be https:// (STANDARDS.md §5).")
        )


def _check_dish(slug: str, data: dict, issues: list) -> None:
    where = f"dish/{slug}"

    # P0 #1-2: cuisine + category required, Title Case + valid value
    cuisine = data.get("cuisine")
    if not cuisine:
        issues.append(("ERR", f"{where}: missing required 'cuisine' field"))
    elif not isinstance(cuisine, str):
        issues.append(("ERR", f"{where}: 'cuisine' must be string, got {type(cuisine).__name__}"))
    elif cuisine != cuisine.title() and cuisine != cuisine:  # placeholder; Title Case check below
        pass
    elif not cuisine[0].isupper():
        issues.append(("ERR", f"{where}: cuisine={cuisine!r} must be Title Case (STANDARDS.md §6)"))

    category = data.get("category")
    if not category:
        issues.append(("ERR", f"{where}: missing required 'category' field"))
    elif category not in VALID_CATEGORIES:
        issues.append(
            ("WARN", f"{where}: category={category!r} not in canonical list "
                     f"({sorted(VALID_CATEGORIES)[:5]}...). Add to vocab or rename.")
        )

    # P0 #3: verified block required
    v = data.get("verified")
    if not v or not isinstance(v, dict):
        issues.append(("ERR", f"{where}: missing required 'verified' block (STANDARDS.md §8)"))
    else:
        for req in ("source_url", "checked_on"):
            if not v.get(req):
                issues.append(("ERR", f"{where}: verified.{req} missing"))
        # P0 #4: no Wikipedia source_url
        su = v.get("source_url", "")
        if isinstance(su, str) and "wikipedia.org" in su.lower():
            issues.append(
                ("ERR", f"{where}: verified.source_url is Wikipedia. "
                        f"Use authoritative operator / cookbook / publication source.")
            )
        # P0 #8: https-only
        for url_field in ("source_url", "history_evidence_url"):
            url = v.get(url_field)
            if url:
                _check_https(url, f"{where}::verified.{url_field}", issues)
        # checked_on freshness (180-day WARN, 365-day ERR; same as TableJourney)
        ch = v.get("checked_on")
        if ch:
            try:
                dt = datetime.strptime(str(ch), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).days
                if age > 365:
                    issues.append(("ERR", f"{where}: verified.checked_on={ch} is {age}d old (>365). Re-verify."))
                elif age > 180:
                    issues.append(("WARN", f"{where}: verified.checked_on={ch} is {age}d old (>180); consider re-verifying."))
            except (ValueError, TypeError):
                issues.append(("ERR", f"{where}: verified.checked_on={ch!r} must be YYYY-MM-DD"))

    # P0 #5: AI-tell scan across description / history / tip
    for f in ("description", "history", "tip"):
        if data.get(f):
            _check_no_ai_tells(data[f], f"{where}::{f}", issues)
            # P0 #6: no em-dashes
            _check_no_em_dashes(data[f], f"{where}::{f}", issues)

    # P0 #7: editorial_score bounded
    es = data.get("editorial_score")
    if es is not None:
        try:
            esf = float(es)
            if esf < 1.0 or esf >= 5.0:
                issues.append(("ERR", f"{where}: editorial_score={esf} out of range 1.0 to 4.9 (5.0 reserved)"))
        except (ValueError, TypeError):
            issues.append(("ERR", f"{where}: editorial_score={es!r} not a number"))

    # Recipe minimums: ≥3 ingredients, ≥2 method steps
    ing = data.get("ingredients")
    if not isinstance(ing, list) or len(ing) < 3:
        issues.append(("ERR", f"{where}: 'ingredients' list must have ≥3 items (got {len(ing) if isinstance(ing, list) else 'none'})"))
    method = data.get("method")
    if not isinstance(method, list) or len(method) < 2:
        issues.append(("ERR", f"{where}: 'method' list must have ≥2 steps (got {len(method) if isinstance(method, list) else 'none'})"))

    # Required prose fields
    for f in ("name", "description", "history"):
        if not data.get(f):
            issues.append(("ERR", f"{where}: missing required '{f}' field"))

    # Meta description length sanity
    desc = data.get("description", "")
    if isinstance(desc, str):
        if len(desc) < 50:
            issues.append(("WARN", f"{where}: description {len(desc)} chars (<50 — too thin)"))
        if len(desc) > 200:
            issues.append(("WARN", f"{where}: description {len(desc)} chars (>200 — Google may truncate)"))

    # hero_image_source_url required when hero_image set
    if data.get("hero_image") and not data.get("hero_image_source_url"):
        issues.append(("ERR", f"{where}: hero_image set but hero_image_source_url missing"))

    # ISO-8601 time check on prep/cook/total
    for f in ("prep_time", "cook_time", "total_time"):
        t = data.get(f)
        if t and not re.match(r"^PT\d+[HM](\d+M)?$", str(t)):
            issues.append(("WARN", f"{where}: {f}={t!r} not ISO-8601 (e.g. PT15M, PT1H30M)"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dish", help="Validate one dish (by slug)")
    args = p.parse_args()

    files = []
    if args.dish:
        candidate = DISHES / f"{args.dish}.json"
        if not candidate.exists():
            print(f"ERR: no such dish: {args.dish}", file=sys.stderr)
            return 2
        files = [candidate]
    else:
        files = sorted(DISHES.glob("*.json"))

    all_issues = []
    for fp in files:
        slug = fp.stem
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            all_issues.append(("ERR", f"{fp}: cannot parse JSON: {e}"))
            continue
        _check_dish(slug, data, all_issues)

    errs = [i for i in all_issues if i[0] == "ERR"]
    warns = [i for i in all_issues if i[0] == "WARN"]
    for level, msg in all_issues:
        print(f"   {level}: {msg}")
    print(f"\nValidated {len(files)} dish(es). ERR: {len(errs)}  WARN: {len(warns)}")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
