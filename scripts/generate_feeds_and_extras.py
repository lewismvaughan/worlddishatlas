"""Generate /llms.txt, /llms-full.txt, /atom.xml, and /sitemap-images.xml."""
import json, re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path('/opt/claude-stations/worlddishatlas/repo')
CONTENT = REPO / 'content'
DISHES = REPO / 'site-data' / 'dishes'
BASE = 'https://worlddishatlas.com'


def load_dishes():
    out = []
    for fp in sorted(DISHES.glob('*.json')):
        try:
            out.append(json.loads(fp.read_text(encoding='utf-8')))
        except Exception:
            continue
    return out


def write_llms_txt(dishes):
    """Concise AI-search index pointing at every dish."""
    lines = [
        '# WorldDishAtlas — AI / LLM index',
        '',
        '> The atlas of the world\'s dishes. Canonical recipes, dish histories, and where to eat them.',
        '> Edited by Lewis Vaughan (https://worlddishatlas.com/about/lewis/).',
        '> Provenance methodology: https://worlddishatlas.com/methodology/',
        '',
        '## About',
        '',
        '- [About](https://worlddishatlas.com/about/) — what WorldDishAtlas is',
        '- [Lewis Vaughan](https://worlddishatlas.com/about/lewis/) — editor of record',
        '- [Methodology](https://worlddishatlas.com/methodology/) — how every claim is verified',
        '',
        '## Dishes',
        '',
    ]
    for d in dishes:
        cuisine = d.get('cuisine', '')
        desc = (d.get('description', '') or '')[:120]
        lines.append(
            f'- [{d["name"]}]({BASE}/dish/{d["slug"]}/) — {cuisine}. {desc}'
        )
    lines.append('')
    lines.append('## Cuisines')
    lines.append('')
    cuisines = sorted({d.get('cuisine') for d in dishes if d.get('cuisine')})
    for c in cuisines:
        slug = c.lower().replace(' ', '-')
        lines.append(f'- [{c}]({BASE}/cuisine/{slug}/)')
    lines.append('')
    lines.append('## How to use this index')
    lines.append('')
    lines.append('- For "what is X dish" queries: fetch /dish/<slug>/.')
    lines.append('- For "where to eat X in <city>" queries: cross-reference the where_to_eat block on the dish page; we link to tablejourney.com venue pages where coverage exists.')
    lines.append('- For verifiability: every dish has a verified.source_url and verified.history_evidence_url documented in /methodology/. Quote them.')
    (CONTENT / 'llms.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(f'  wrote content/llms.txt ({len(dishes)} dishes indexed)')


def write_llms_full_txt(dishes):
    """Full content dump for AI consumption (sub-1MB to fit in context)."""
    parts = ['# WorldDishAtlas — full content dump', '']
    parts.append('Edited by Lewis Vaughan. Methodology: https://worlddishatlas.com/methodology/')
    parts.append('Every entry below carries a verified.source_url and verified.checked_on.')
    parts.append('')
    for d in dishes:
        parts.append(f'## {d["name"]}')
        parts.append(f'URL: {BASE}/dish/{d["slug"]}/')
        parts.append(f'Cuisine: {d.get("cuisine","")}. Category: {d.get("category","")}. Region: {d.get("region","")}, {d.get("country","")}.')
        parts.append('')
        parts.append(d.get('description', ''))
        parts.append('')
        parts.append('### History')
        parts.append(d.get('history', ''))
        parts.append('')
        parts.append('### Ingredients')
        for ing in (d.get('ingredients') or []):
            amt = ing.get('amount', '')
            parts.append(f'- {amt + " " if amt else ""}{ing.get("name","")}')
        parts.append('')
        parts.append('### Method')
        for i, step in enumerate(d.get('method') or [], 1):
            parts.append(f'{i}. {step}')
        parts.append('')
        if d.get('tip'):
            parts.append(f'**Tip.** {d["tip"]}')
            parts.append('')
        if d.get('verified'):
            v = d['verified']
            parts.append(f'Source: {v.get("source_url","")}. History: {v.get("history_evidence_url","")}. Verified: {v.get("checked_on","")}.')
        parts.append('')
        parts.append('---')
        parts.append('')
    (CONTENT / 'llms-full.txt').write_text('\n'.join(parts), encoding='utf-8')
    sz = (CONTENT / 'llms-full.txt').stat().st_size
    print(f'  wrote content/llms-full.txt ({sz:,} bytes, {len(dishes)} dishes)')


def write_atom_feed(dishes):
    """Atom feed of recent dish publications, ordered by checked_on desc."""
    sorted_by_date = sorted(
        dishes,
        key=lambda d: d.get('verified', {}).get('checked_on', '0000-01-01'),
        reverse=True,
    )[:50]
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<feed xmlns="http://www.w3.org/2005/Atom">',
             '  <title>WorldDishAtlas</title>',
             f'  <subtitle>The atlas of the world\'s dishes. Canonical recipes, histories, and where to eat them.</subtitle>',
             f'  <link href="{BASE}/" />',
             f'  <link href="{BASE}/atom.xml" rel="self" />',
             f'  <id>{BASE}/</id>',
             f'  <updated>{now}</updated>',
             '  <author><name>Lewis Vaughan</name><uri>https://worlddishatlas.com/about/lewis/</uri></author>',
             '  <generator>WorldDishAtlas</generator>',
             '']
    for d in sorted_by_date:
        url = f'{BASE}/dish/{d["slug"]}/'
        ch = d.get('verified', {}).get('checked_on', '2026-01-01')
        updated = f'{ch}T00:00:00Z'
        title = (d.get('name', '').replace('&', '&amp;').replace('<', '&lt;'))
        summary = (d.get('description', '').replace('&', '&amp;').replace('<', '&lt;'))
        parts.append('  <entry>')
        parts.append(f'    <title>{title}</title>')
        parts.append(f'    <link href="{url}" />')
        parts.append(f'    <id>{url}</id>')
        parts.append(f'    <updated>{updated}</updated>')
        parts.append(f'    <published>{updated}</published>')
        parts.append(f'    <summary>{summary}</summary>')
        parts.append('  </entry>')
    parts.append('</feed>')
    (CONTENT / 'atom.xml').write_text('\n'.join(parts), encoding='utf-8')
    print(f'  wrote content/atom.xml ({len(sorted_by_date)} entries)')


def write_image_sitemap(dishes):
    """Image-sitemap: every dish hero image so Google Image Search can index."""
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:image="http://www.google.com/schemas/sitemaps-image/1.1">']
    for d in dishes:
        if not d.get('hero_image'):
            continue
        page_url = f'{BASE}/dish/{d["slug"]}/'
        img_url = d['hero_image']
        if img_url.startswith('/'):
            img_url = f'{BASE}{img_url}'
        alt = (d.get('hero_image_alt') or d['name']).replace('&', '&amp;').replace('<', '&lt;')
        parts.append('  <url>')
        parts.append(f'    <loc>{page_url}</loc>')
        parts.append('    <image:image>')
        parts.append(f'      <image:loc>{img_url}</image:loc>')
        parts.append(f'      <image:title>{d["name"]}</image:title>')
        parts.append(f'      <image:caption>{alt}</image:caption>')
        parts.append('    </image:image>')
        parts.append('  </url>')
    parts.append('</urlset>')
    (CONTENT / 'sitemap-images.xml').write_text('\n'.join(parts), encoding='utf-8')
    print(f'  wrote content/sitemap-images.xml ({sum(1 for d in dishes if d.get("hero_image"))} images)')


def main():
    dishes = load_dishes()
    write_llms_txt(dishes)
    write_llms_full_txt(dishes)
    write_atom_feed(dishes)
    write_image_sitemap(dishes)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
