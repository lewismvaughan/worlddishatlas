#!/usr/bin/env python3
"""Generate all index + hub pages: /dish/, /cuisine/, /cuisine/<slug>/,
/ingredient/, /ingredient/<slug>/, /category/<slug>/.

One script for all hub-style pages because they share data + template.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
TEMPLATES = REPO / "templates"
DISHES = REPO / "site-data" / "dishes"
BASE = "https://worlddishatlas.com"


def collect():
    rows = []
    for fp in sorted(DISHES.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            rows.append(d)
        except Exception:
            continue
    return rows


def render_hub(env, slug_path: str, title: str, h1: str, subtitle: str,
               meta_desc: str, dishes: list, breadcrumb: list) -> Path:
    page = {
        "title": f"{title} | WorldDishAtlas",
        "meta_description": meta_desc,
        "canonical_url": f"{BASE}/{slug_path}/" if slug_path else f"{BASE}/",
        "og_image": f"{BASE}/img/og-default.jpg",
        "og_type": "website",
        "h1": h1,
        "subtitle": subtitle,
        "breadcrumb_items": breadcrumb,
        "page_type": "collection",
    }
    tpl = env.get_template("hub.html")
    html = tpl.render(page=page, dishes=dishes)
    out = CONTENT / slug_path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def render_index(env, slug_path: str, title: str, h1: str, subtitle: str,
                 meta_desc: str, items: list, item_kind: str, breadcrumb: list) -> Path:
    page = {
        "title": f"{title} | WorldDishAtlas",
        "meta_description": meta_desc,
        "canonical_url": f"{BASE}/{slug_path}/",
        "og_image": f"{BASE}/img/og-default.jpg",
        "og_type": "website",
        "h1": h1,
        "subtitle": subtitle,
        "breadcrumb_items": breadcrumb,
        "page_type": "collection",
    }
    tpl = env.get_template("index_grid.html")
    html = tpl.render(page=page, items=items, item_kind=item_kind)
    out = CONTENT / slug_path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html"]))
    dishes = collect()

    # 1) /dish/ — list every dish A-Z
    sorted_dishes = sorted(dishes, key=lambda d: d["name"].lower())
    render_hub(env, "dish",
               "All dishes",
               "Every dish on WorldDishAtlas",
               f"{len(sorted_dishes)} dishes and counting.",
               f"Every dish on WorldDishAtlas, A to Z. Canonical recipes, the history of each dish, variations, and where to eat the canonical version.",
               sorted_dishes,
               [{"name": "Home", "url": f"{BASE}/"},
                {"name": "Dishes"}])
    print(f"  wrote content/dish/index.html ({len(sorted_dishes)} dishes)")

    # 2) /cuisine/ — index of cuisines
    cuisine_counts = Counter(d["cuisine"] for d in dishes if d.get("cuisine"))
    cuisine_items = [{"name": c, "slug": c.lower().replace(" ", "-"),
                       "url": f"/cuisine/{c.lower().replace(' ', '-')}/",
                       "count": n,
                       "subtitle": f"{n} dish{'es' if n != 1 else ''}"}
                      for c, n in cuisine_counts.most_common()]
    render_index(env, "cuisine",
                 "Cuisines",
                 "Browse by cuisine",
                 "Every cuisine covered on WorldDishAtlas.",
                 "Browse WorldDishAtlas by cuisine. Italian, Japanese, Thai, Mexican, Vietnamese, and more. Every dish with canonical recipes and dish histories.",
                 cuisine_items, "cuisine",
                 [{"name": "Home", "url": f"{BASE}/"},
                  {"name": "Cuisines"}])
    print(f"  wrote content/cuisine/index.html ({len(cuisine_items)} cuisines)")

    # 3) /cuisine/<slug>/ — per-cuisine hub
    by_cuisine = defaultdict(list)
    for d in dishes:
        if d.get("cuisine"):
            by_cuisine[d["cuisine"]].append(d)
    for cuisine, dlist in by_cuisine.items():
        slug = cuisine.lower().replace(" ", "-")
        render_hub(env, f"cuisine/{slug}",
                   f"{cuisine} dishes",
                   f"{cuisine} dishes",
                   f"The {cuisine.lower()} canon, dish by dish.",
                   f"Every {cuisine} dish on WorldDishAtlas. Canonical recipes, dish histories, variations, and where to eat each at its source. Verified, edited by humans.",
                   sorted(dlist, key=lambda d: d["name"]),
                   [{"name": "Home", "url": f"{BASE}/"},
                    {"name": "Cuisines", "url": f"{BASE}/cuisine/"},
                    {"name": cuisine}])
    print(f"  wrote {len(by_cuisine)} per-cuisine hub pages")

    # 4) /ingredient/ index + per-ingredient pages
    ingredient_counts = Counter()
    by_ingredient = defaultdict(list)
    for d in dishes:
        for ing in (d.get("core_ingredients") or []):
            ingredient_counts[ing] += 1
            by_ingredient[ing].append(d)
    ingredient_items = [{"name": i.replace("-", " ").title(), "slug": i,
                          "url": f"/ingredient/{i}/", "count": n,
                          "subtitle": f"in {n} dish{'es' if n != 1 else ''}"}
                         for i, n in ingredient_counts.most_common()]
    render_index(env, "ingredient",
                 "Ingredients",
                 "Browse by ingredient",
                 "Discover dishes by the ingredients they share.",
                 "Browse WorldDishAtlas by ingredient. Find every dish that uses guanciale, fish sauce, tamarind, kombu, achiote, and more. Cross-cuisine discovery.",
                 ingredient_items, "ingredient",
                 [{"name": "Home", "url": f"{BASE}/"},
                  {"name": "Ingredients"}])
    print(f"  wrote content/ingredient/index.html ({len(ingredient_items)} ingredients)")
    for ing, dlist in by_ingredient.items():
        name = ing.replace("-", " ").title()
        render_hub(env, f"ingredient/{ing}",
                   f"Dishes with {name}",
                   f"Dishes with {name}",
                   f"Every dish on WorldDishAtlas built around {name.lower()}.",
                   f"Every dish on WorldDishAtlas built around {name.lower()}. Canonical recipes, cuisines that use it, and where to eat each dish at its source.",
                   sorted(dlist, key=lambda d: d["name"]),
                   [{"name": "Home", "url": f"{BASE}/"},
                    {"name": "Ingredients", "url": f"{BASE}/ingredient/"},
                    {"name": name}])
    print(f"  wrote {len(by_ingredient)} per-ingredient hub pages")

    # 5) /category/<slug>/ — per-category
    by_category = defaultdict(list)
    for d in dishes:
        if d.get("category"):
            by_category[d["category"]].append(d)
    for cat, dlist in by_category.items():
        slug = cat.lower().replace(" ", "-")
        render_hub(env, f"category/{slug}",
                   f"{cat.title()} dishes",
                   f"{cat.title()} dishes",
                   f"The {cat} canon, dish by dish.",
                   f"Every {cat} dish on WorldDishAtlas. Canonical recipes, dish histories, regional variations, and where to eat. Edited by humans, verified provenance.",
                   sorted(dlist, key=lambda d: d["name"]),
                   [{"name": "Home", "url": f"{BASE}/"},
                    {"name": cat.title()}])
    print(f"  wrote {len(by_category)} per-category hub pages")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
