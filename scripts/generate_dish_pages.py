#!/usr/bin/env python3
"""Render every dish JSON into content/dish/<slug>/index.html.

URL pattern: worlddishatlas.com/dish/<slug>/

Usage:
    python3 scripts/generate_dish_pages.py --all
    python3 scripts/generate_dish_pages.py --dish carbonara
"""

import argparse
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parent.parent
DISHES = REPO / "site-data" / "dishes"
TEMPLATES = REPO / "templates"
OUT = REPO / "content" / "dish"
BASE_URL = "https://worlddishatlas.com"



def _existing_dish_slugs():
    return {p.stem for p in DISHES.glob('*.json')}


def render_dish(env, slug: str, data: dict) -> Path:
    canonical = f"{BASE_URL}/dish/{slug}/"
    page = {
        "title": f"{data['name']} | WorldDishAtlas",
        "meta_description": data["description"][:160],
        "canonical_url": canonical,
        "og_image": data.get("hero_image_absolute") or f"{BASE_URL}{data.get('hero_image', '/img/og-default.jpg')}",
        "og_image_alt": data.get("hero_image_alt") or data["name"],
        "og_type": "article",
        "breadcrumb_items": [
            {"name": "Home", "url": f"{BASE_URL}/"},
            {"name": "Dishes", "url": f"{BASE_URL}/dish/"},
            {"name": data["cuisine"], "url": f"{BASE_URL}/cuisine/{data['cuisine'].lower().replace(' ', '-')}/"},
            {"name": data["name"]},
        ],
    }
    # Filter related/compared dish slugs to only those that exist
    existing = _existing_dish_slugs()
    for f in ("related_dishes", "compared_to"):
        vals = data.get(f) or []
        data[f] = [s for s in vals if s in existing]
    tpl = env.get_template("dish.html")
    html = tpl.render(dish=data, page=page)
    out_path = OUT / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true")
    p.add_argument("--dish", help="One dish slug")
    args = p.parse_args()

    if not args.all and not args.dish:
        print("Pass --all or --dish <slug>", file=sys.stderr)
        return 2

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )

    if args.dish:
        files = [DISHES / f"{args.dish}.json"]
    else:
        files = sorted(DISHES.glob("*.json"))

    rendered = 0
    for fp in files:
        if not fp.exists():
            print(f"  skip: {fp} (missing)")
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  skip: {fp.name} (parse err: {e})")
            continue
        out = render_dish(env, fp.stem, data)
        print(f"  wrote {out.relative_to(REPO)}")
        rendered += 1
    print(f"\nDONE. rendered={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
