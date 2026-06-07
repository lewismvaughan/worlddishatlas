#!/usr/bin/env python3
"""Generate /compare/<a>-vs-<b>/ pages from compared_to fields.

For every dish with `compared_to: [slug, slug, ...]`, render the
comparison page in canonical alphabetical order (a-vs-b, never b-vs-a).
Dedup pairs so each combo only renders once.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / 'content'
TEMPLATES = REPO / 'templates'
DISHES = REPO / 'site-data' / 'dishes'
BASE = 'https://worlddishatlas.com'


def load_all():
    out = {}
    for fp in sorted(DISHES.glob('*.json')):
        try:
            d = json.loads(fp.read_text(encoding='utf-8'))
            out[d['slug']] = d
        except Exception:
            continue
    return out


def render_comparison(env, a, b, now_iso):
    # canonical order: sort by slug
    if a['slug'] > b['slug']:
        a, b = b, a
    slug = f"{a['slug']}-vs-{b['slug']}"
    canonical = f"{BASE}/compare/{slug}/"

    shared = sorted(set(a.get('core_ingredients') or []) & set(b.get('core_ingredients') or []))
    same_cuisine = a.get('cuisine') == b.get('cuisine')
    same_category = a.get('category') == b.get('category')

    if same_cuisine and same_category:
        intro = (f"{a['name']} and {b['name']} are both {a['cuisine']} {a['category']} dishes. "
                 f"They share an audience and most readers want to know what actually separates them.")
    elif same_cuisine:
        intro = (f"{a['name']} and {b['name']} both come out of {a['cuisine']} cooking but they sit in "
                 f"different chapters. {a['name']} is a {a['category']} dish; {b['name']} is a {b['category']}.")
    else:
        intro = (f"{a['name']} ({a['cuisine']}) and {b['name']} ({b['cuisine']}) are different cuisines "
                 f"that get compared on menus and search results. Here is what actually separates them.")

    if shared:
        short = f"Both dishes use {', '.join(s.replace('-',' ') for s in shared[:3])}. {a['description'][:100]}... {b['description'][:100]}..."
    else:
        short = f"Almost no overlap. {a['description'][:140]}"

    page = {
        'title': f"{a['name']} vs {b['name']} | WorldDishAtlas",
        'meta_description': (f"{a['name']} vs {b['name']}. Cuisine, ingredients, technique, and where each comes from. "
                              f"The side-by-side guide, with full recipes for both.")[:158],
        'canonical_url': canonical,
        'og_image': f'{BASE}/img/og-default.jpg',
        'og_type': 'article',
        'h1': f'{a["name"]} vs {b["name"]}',
        'breadcrumb_items': [
            {'name': 'Home', 'url': f'{BASE}/'},
            {'name': 'Compare', 'url': f'{BASE}/compare/'},
            {'name': f'{a["name"]} vs {b["name"]}'},
        ],
    }
    tpl = env.get_template('compare.html')
    html = tpl.render(page=page, a=a, b=b, intro=intro,
                      short_version=short, shared_ingredients=shared,
                      now_iso=now_iso)
    out = CONTENT / 'compare' / slug / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    return slug, out


def render_compare_index(env, pairs):
    """Index page listing every comparison."""
    page = {
        'title': 'Dish comparisons | WorldDishAtlas',
        'meta_description': 'Side-by-side comparisons of dishes that get confused. Carbonara vs cacio e pepe, ramen vs pho, pad thai vs pad see ew, and more.'[:158],
        'canonical_url': f'{BASE}/compare/',
        'og_image': f'{BASE}/img/og-default.jpg',
        'og_type': 'website',
        'h1': 'Dish comparisons',
        'subtitle': 'Side by side. What\'s actually different.',
        'breadcrumb_items': [
            {'name': 'Home', 'url': f'{BASE}/'},
            {'name': 'Compare'},
        ],
        'page_type': 'collection',
    }
    items = [{'name': f"{pair[0]['name']} vs {pair[1]['name']}",
              'slug': pair[2],
              'url': f"/compare/{pair[2]}/",
              'count': len(set(pair[0].get('core_ingredients') or []) & set(pair[1].get('core_ingredients') or [])),
              'subtitle': f"{pair[0]['cuisine']} vs {pair[1]['cuisine']}"}
             for pair in pairs]
    tpl = env.get_template('index_grid.html')
    html = tpl.render(page=page, items=items, item_kind='comparison')
    out = CONTENT / 'compare' / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')


def main():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(['html']))
    dishes = load_all()
    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    seen_pairs = set()
    pairs = []
    for slug, d in dishes.items():
        for other in (d.get('compared_to') or []):
            if other not in dishes:
                continue
            key = tuple(sorted([slug, other]))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            a, b = dishes[key[0]], dishes[key[1]]
            comparison_slug, _ = render_comparison(env, a, b, now_iso)
            pairs.append((a, b, comparison_slug))
            print(f'  wrote content/compare/{comparison_slug}/index.html')

    render_compare_index(env, pairs)
    print(f'  wrote content/compare/index.html ({len(pairs)} comparisons)')
    print(f'DONE. {len(pairs)} comparison pages rendered.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
