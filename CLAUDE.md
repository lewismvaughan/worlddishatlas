# WorldDishAtlas station (claude code-management workstation for worlddishatlas.com)

You manage the live code AND the live site of **worlddishatlas.com**, a
static SEO-driven encyclopedia of global dishes. The site exploits the
high search volume on "what is X dish" / "how to make X" / "X vs Y"
queries with editor-verified, AI-assisted content.

Sister site to **tablejourney.com** (the where-to-eat layer). WorldDishAtlas
is the **what-is-it / how-do-you-make-it** layer.

## READ FIRST (before any non-trivial work)

1. **[docs/STANDARDS.md](docs/STANDARDS.md)** — SEO + content invariants
   every generator and agent must respect. Includes the 9 P0 rules
   inherited from TableJourney Rounds 6-10 audits (no AI tells, no em
   dashes, cuisine taxonomy Title Case, no Wikipedia source_urls for
   dishes, no TBA placeholders, editorial_score < 5.0, hero_image_source_url
   required, https-only URLs, festival year auto-roll).
2. **[docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md)** — dish JSON structure,
   schema.org Recipe + Article emission rules, verified-block contract.
3. **[docs/FLOW.md](docs/FLOW.md)** — research → QA → ship pipeline,
   ported from TableJourney's proven 5-stage canonical pipeline.

## What WorldDishAtlas is

- A Python-based **static-site generator** (Jinja2 + per-dish JSON
  files rendered to HTML under `content/`).
- Public-facing at **https://worlddishatlas.com**
- Authored by Lewis Vaughan (same Person schema as TableJourney; cross-
  links to /about/lewis/ on both sites).

## Hosting layout on server-3

Same pattern as TableJourney. No app process. Caddy serves the built
HTML directly. Any change under `content/` is live immediately with no
build / restart / deploy step.

| Path | Purpose |
|------|---------|
| `/opt/claude-stations/worlddishatlas/repo/` | Repo root |
| `/opt/claude-stations/worlddishatlas/repo/content/` | Caddy serves from here; URLs map 1:1 to files |
| `/opt/claude-stations/worlddishatlas/repo/templates/` | Jinja2 sources |
| `/opt/claude-stations/worlddishatlas/repo/site-data/dishes/` | Per-dish JSON (one file per dish) |
| `/opt/claude-stations/worlddishatlas/repo/scripts/` | Generators, validators, sitemap |

## URL conventions

- Home: `/`
- Dish (canonical): `/dish/<dish-slug>/`
- Cuisine hub: `/cuisine/<cuisine-slug>/`
- Cuisine variant of dish: `/cuisine/<cuisine-slug>/<dish-slug>/`
- Ingredient page: `/ingredient/<ingredient-slug>/`
- Comparison: `/compare/<dish-a>-vs-<dish-b>/`
- Author: `/about/lewis/` (mirrors TableJourney)
- Methodology: `/methodology/`
- Sitemap: `/sitemap.xml`, robots: `/robots.txt`, AI: `/llms.txt`

## The 9 P0 rules inherited from TableJourney

Every dish + every generated page must respect these (validate_data.py
hard-fails on violations):

1. **`cuisine` field required** on every dish (Title Case, e.g. "Italian")
2. **`category` field required** (e.g. "pasta", "soup", "dessert")
3. **`verified` block required** with source_url, history_evidence_url,
   checked_on
4. **No Wikipedia source_url** for the recipe / dish-page main source
5. **No AI-tell phrases** in description / history / tip prose:
   - "hidden gem", "must-try", "world-class", "nestled in",
   - "to die for", "iconic", "culinary journey", "second to none",
   - "unparalleled", "a must visit", "wide selection"
6. **No em-dashes (—) or en-dashes (–)** in any content
7. **`editorial_score` bounded 1.0 to 4.9** (5.0 reserved)
8. **HTTPS-only** for all source URLs
9. **Hours / dates** in 24-hour or ISO format if present

## What every page emits

- `<title>` ≤ 65 chars, unique across the site
- `<meta description>` 120-160 chars, unique
- Canonical tag, self-referencing
- Open Graph: image, title, description, type (article/website)
- Twitter card: summary_large_image
- JSON-LD: schema.org Article + Recipe + BreadcrumbList + Person (author)
  — and ImageObject + ItemList where applicable
- Visible "Last verified [date]" pulled from verified.checked_on
- `inLanguage: "en"` in JSON-LD
- `award` field on dish-page Recipe schema when entity carries credentials

## Building new content

1. Add a dish JSON at `site-data/dishes/<slug>.json` matching the
   schema in docs/DATA_SCHEMA.md
2. `python3 scripts/validate_data.py --dish <slug>` — must PASS
3. `python3 scripts/check_jsonld.py` after generation
4. `python3 scripts/generate_dish_pages.py --all` (or `--dish <slug>`)
5. `python3 scripts/generate_sitemap.py`
6. `chmod -R a+rX content/` (so Caddy can serve)

## What to NOT do

- Do not put secrets / credentials anywhere under `content/`
  (everything in `content/` is publicly served)
- Do not change Caddyfile without asking Lewis
- Do not commit personal URLs as hardcoded strings (use env vars like
  TableJourney's TJ_LEWIS_LINKEDIN_URL / TJ_LEWIS_GITHUB_URL)
- Do not generate AI content without the verified-block + human sign-off
  pattern. Same rule as TableJourney.
