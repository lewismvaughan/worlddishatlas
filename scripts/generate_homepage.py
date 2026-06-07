#!/usr/bin/env python3
"""Render content/index.html from all available dishes."""

import json
import os
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _analytics():
    return {
        "gtm_id": os.environ.get("WDA_GTM_CONTAINER_ID", ""),
        "clarity_id": os.environ.get("WDA_CLARITY_PROJECT_ID", ""),
        "gsc_token": os.environ.get("WDA_GSC_VERIFICATION", ""),
        "bing_token": os.environ.get("WDA_BING_VERIFICATION", ""),
    }

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
TEMPLATES = REPO / "templates"
DISHES = REPO / "site-data" / "dishes"
BASE = "https://worlddishatlas.com"


def collect_dishes():
    rows = []
    for fp in sorted(DISHES.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows.append(d)
    return rows


def main() -> int:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html"]))
    dishes = collect_dishes()

    # Featured: top 12 by editorial_score
    featured = sorted(
        [d for d in dishes if d.get("editorial_score")],
        key=lambda d: (-float(d["editorial_score"]), d["name"]),
    )[:12]

    # Cuisine counts
    cuisine_counts = Counter()
    for d in dishes:
        if d.get("cuisine"):
            cuisine_counts[d["cuisine"]] += 1
    cuisines = [
        {"name": c, "slug": c.lower().replace(" ", "-"), "count": n}
        for c, n in cuisine_counts.most_common(30)
    ]

    # Category counts
    category_counts = Counter()
    for d in dishes:
        if d.get("category"):
            category_counts[d["category"]] += 1
    categories = [
        {"name": c, "slug": c.lower().replace(" ", "-"), "count": n}
        for c, n in category_counts.most_common(20)
    ]

    page = {
        "title": "WorldDishAtlas — the atlas of the world's dishes",
        "meta_description": (
            "Canonical recipes, dish histories, and where to eat them. "
            "The encyclopedia of the world's dishes. Edited by humans."
        ),
        "canonical_url": f"{BASE}/",
        "og_image": f"{BASE}/img/og-default.jpg",
        "og_image_alt": "WorldDishAtlas — global dish encyclopedia",
        "og_type": "website",
        "breadcrumb_items": [],
    }
    tpl = env.get_template("home.html")
    html = tpl.render(analytics=_analytics(), 
        page=page,
        featured_dishes=featured,
        cuisines=cuisines,
        categories=categories,
    )
    out = CONTENT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  wrote {out.relative_to(REPO)} ({len(dishes)} dishes seen)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
