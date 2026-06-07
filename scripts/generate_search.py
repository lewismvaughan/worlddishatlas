#!/usr/bin/env python3
"""Build content/search/search-index.json from every dish + cuisine +
ingredient + category. Client-side fuzzy ranker consumes this.

For sub-100 entities this is plenty fast as a single JSON file. Scale
later (shard by first letter) only if we cross ~5K entries.
"""

import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
DISHES = REPO / "site-data" / "dishes"
BASE = "https://worlddishatlas.com"


def normalize(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. Match client side."""
    import unicodedata, re
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> int:
    entries = []
    dishes = []
    for fp in sorted(DISHES.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        dishes.append(d)

    # Dishes
    for d in dishes:
        tokens = " ".join([
            d.get("name", ""),
            d.get("name_native", ""),
            d.get("cuisine", ""),
            d.get("region", ""),
            d.get("country", ""),
            d.get("category", ""),
            " ".join(d.get("core_ingredients") or []),
        ])
        entries.append({
            "id": f"dish:{d['slug']}",
            "type": "dish",
            "name": d["name"],
            "subtitle": f"{d.get('cuisine','')} · {d.get('category','').title()}",
            "url": f"/dish/{d['slug']}/",
            "tokens": normalize(tokens),
            "weight": 10,
        })

    # Cuisines
    cuisines = Counter(d["cuisine"] for d in dishes if d.get("cuisine"))
    for c, n in cuisines.items():
        slug = c.lower().replace(" ", "-")
        entries.append({
            "id": f"cuisine:{slug}",
            "type": "cuisine",
            "name": c,
            "subtitle": f"{n} dish{'es' if n != 1 else ''}",
            "url": f"/cuisine/{slug}/",
            "tokens": normalize(f"{c} cuisine"),
            "weight": 8,
        })

    # Ingredients
    ing_counts = Counter()
    for d in dishes:
        for i in (d.get("core_ingredients") or []):
            ing_counts[i] += 1
    for i, n in ing_counts.items():
        entries.append({
            "id": f"ingredient:{i}",
            "type": "ingredient",
            "name": i.replace("-", " ").title(),
            "subtitle": f"in {n} dish{'es' if n != 1 else ''}",
            "url": f"/ingredient/{i}/",
            "tokens": normalize(i.replace("-", " ")),
            "weight": 6,
        })

    # Categories
    cat_counts = Counter(d["category"] for d in dishes if d.get("category"))
    for c, n in cat_counts.items():
        slug = c.lower().replace(" ", "-")
        entries.append({
            "id": f"category:{slug}",
            "type": "category",
            "name": c.title(),
            "subtitle": f"{n} dish{'es' if n != 1 else ''}",
            "url": f"/category/{slug}/",
            "tokens": normalize(c),
            "weight": 7,
        })

    # Chrome
    for url, name, sub in [
        ("/about/", "About", "About WorldDishAtlas"),
        ("/about/lewis/", "Lewis Vaughan", "Founder and editor"),
        ("/methodology/", "Methodology", "How every claim is verified"),
        ("/contact/", "Contact", "Reach the editorial desk"),
    ]:
        entries.append({
            "id": f"chrome:{url}",
            "type": "chrome",
            "name": name,
            "subtitle": sub,
            "url": url,
            "tokens": normalize(f"{name} {sub}"),
            "weight": 4,
        })

    out_dir = CONTENT / "search"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "search-index.json").write_text(
        json.dumps({"entries": entries}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  wrote content/search/search-index.json ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
