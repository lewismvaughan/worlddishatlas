#!/usr/bin/env python3
"""Validate every JSON-LD block on every rendered HTML page.

Critical: uses object_pairs_hook to detect DUPLICATE properties before
json.loads silently collapses them. Google rejects "Duplicate unique
property" with no rich-results eligibility. This caught 18 TableJourney
pages on 2026-06-07; WorldDishAtlas ships with the check from day 1.

Usage:
    python3 scripts/check_jsonld.py
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL,
)

REQUIRED_FIELDS_BY_TYPE = {
    "Recipe": ("name", "image", "recipeIngredient", "recipeInstructions", "author", "datePublished"),
    "Article": ("headline", "datePublished", "author", "publisher", "image"),
    "BreadcrumbList": ("itemListElement",),
    "Person": ("name",),
}


def _detect_dupes_factory(trail: list):
    def _hook(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                trail.append(k)
            seen[k] = v
        return seen
    return _hook


def _flatten_items(node):
    if isinstance(node, dict):
        if "@type" in node:
            yield node
        if "@graph" in node:
            yield from _flatten_items(node["@graph"])
    elif isinstance(node, list):
        for item in node:
            yield from _flatten_items(item)


def main() -> int:
    pages = list(CONTENT.rglob("*.html"))
    total_blocks = 0
    issues_by_page = []
    type_counts = Counter()

    for f in sorted(pages):
        if not f.is_file():
            continue
        try:
            html = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        url = "/" + str(f.parent.relative_to(CONTENT)).replace("\\", "/") + "/"
        blocks = JSONLD_RE.findall(html)
        page_issues = []
        for i, raw in enumerate(blocks):
            total_blocks += 1
            dup_keys = []
            try:
                payload = json.loads(raw, object_pairs_hook=_detect_dupes_factory(dup_keys))
            except json.JSONDecodeError as e:
                page_issues.append(f"block #{i}: invalid JSON ({e})")
                continue
            if dup_keys:
                page_issues.append(
                    f"block #{i}: duplicate JSON-LD property/properties "
                    f"{sorted(set(dup_keys))} (Google rejects 'Duplicate "
                    f"unique property' for rich results)"
                )
            for item in _flatten_items(payload):
                t = item.get("@type")
                if isinstance(t, list):
                    for tt in t:
                        type_counts[tt] += 1
                elif isinstance(t, str):
                    type_counts[t] += 1
                    req = REQUIRED_FIELDS_BY_TYPE.get(t)
                    if req:
                        missing = [r for r in req if not item.get(r)]
                        if missing:
                            page_issues.append(
                                f"block #{i}: {t} missing required field(s): {missing}"
                            )
        if not blocks:
            page_issues.append("no JSON-LD blocks found")
        if page_issues:
            issues_by_page.append({"url": url, "issues": page_issues})

    print(f"Pages scanned: {len(pages)}")
    print(f"JSON-LD blocks: {total_blocks}")
    print(f"\n@type counts:")
    for t, n in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:5d}  {t}")
    print(f"\nPages with issues: {len(issues_by_page)}")
    for row in issues_by_page[:30]:
        print(f"  {row['url']}")
        for issue in row["issues"][:3]:
            print(f"    - {issue}")
    if len(issues_by_page) > 30:
        print(f"  ... and {len(issues_by_page) - 30} more pages")

    out_path = Path("/tmp/wda_jsonld.json")
    out_path.write_text(json.dumps({
        "pages_scanned": len(pages),
        "total_blocks": total_blocks,
        "type_counts": dict(type_counts),
        "issues_by_page": issues_by_page,
    }, indent=2), encoding="utf-8")
    print(f"\nFull report: {out_path}")
    return 1 if issues_by_page else 0


if __name__ == "__main__":
    raise SystemExit(main())
