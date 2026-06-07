# WorldDishAtlas

The atlas of the world's dishes. Canonical recipes, dish histories, and
where to eat them. Sister site to [TableJourney](https://tablejourney.com).

Edited by [Lewis Vaughan](https://worlddishatlas.com/about/lewis/).
Built on a verified-provenance pipeline with full human editor sign-off.
See the [methodology page](https://worlddishatlas.com/methodology/) for
how every claim gets verified.

## Stack

Static site generator: Python + Jinja2. No app server, no database,
nothing dynamic. Caddy serves the rendered HTML from `content/` directly.

## Repo layout

```
worlddishatlas/
├── CLAUDE.md                 # workstation guide
├── docs/
│   ├── STANDARDS.md          # 9 P0 rules every page must respect
│   └── DATA_SCHEMA.md        # dish JSON structure
├── scripts/
│   ├── validate_data.py      # 9-rule hard-fail validator
│   ├── check_jsonld.py       # rendered HTML JSON-LD validator
│   ├── generate_dish_pages.py
│   ├── generate_indexes.py   # hubs: dish/, cuisine/, ingredient/, category/
│   ├── generate_homepage.py
│   ├── generate_chrome_pages.py # about, lewis, methodology, legal
│   └── generate_sitemap.py   # sitemap.xml + robots.txt
├── templates/
│   ├── base.html
│   ├── dish.html
│   ├── hub.html              # cuisine + ingredient + category hubs
│   ├── index_grid.html       # cuisines + ingredients indexes
│   ├── home.html
│   └── chrome/page.html
├── site-data/
│   └── dishes/               # one JSON per dish
├── content/                  # rendered HTML, served by Caddy
│   ├── index.html
│   ├── dish/<slug>/
│   ├── cuisine/<slug>/
│   ├── ingredient/<slug>/
│   ├── category/<slug>/
│   ├── about/, methodology/, contact/, privacy/, terms/, ...
│   ├── css/, img/
│   └── sitemap.xml, robots.txt, favicon.svg, site.webmanifest
└── agents/dish-research/PROMPT.md  # research-agent brief
```

## Build flow

```bash
# Validate every dish
python3 scripts/validate_data.py

# Render pages
python3 scripts/generate_dish_pages.py --all
python3 scripts/generate_homepage.py
python3 scripts/generate_indexes.py
python3 scripts/generate_chrome_pages.py
python3 scripts/generate_sitemap.py

# Audit rendered JSON-LD (catches duplicate properties + missing fields)
python3 scripts/check_jsonld.py

# Make Caddy-readable
chmod -R a+rX content/
```

Or chain via the standard ship pattern (when wired up).

## Hardening inherited from TableJourney

Built from day 1 with every defect class TableJourney hardened against
over its Rounds 6-12 site-wide audits and Google Search Console
validation work:

- 9 P0 rules in `validate_data.py` (cuisine required, category required,
  verified block required, no Wikipedia source_urls, no AI tells, no
  em-dashes, editorial_score < 5.0, https-only, hero_image_source_url
  required)
- `check_jsonld.py` uses `object_pairs_hook` to catch duplicate JSON-LD
  properties before parse silently collapses them (the bug Google flagged
  on 18 TableJourney pages on 2026-06-07)
- Person JSON-LD on `/about/lewis/` with `sameAs` to LinkedIn + GitHub
  (env-var driven so personal URLs stay out of the repo)
- Visible "Last verified" date on every dish page pulled from
  `verified.checked_on`
- `inLanguage: "en"` on every schema block
- Mobile-first responsive CSS, hero `fetchpriority="high"`, below-fold
  `loading="lazy"`

## License

Editorial content: copyright WorldDishAtlas. Quote freely with
attribution; do not republish wholesale without written permission.

Code: MIT.
