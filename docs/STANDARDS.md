# WorldDishAtlas — SEO + content standards

The invariants every page, every generator, every content commit must
respect. Lifted from TableJourney's hard-won 11 audit rounds + GSC
validation work; pre-baked so we never re-learn them.

## 1. Page schema completeness (required for rich results)

Every dish page must emit JSON-LD with:
- `Article` (the editorial wrapper)
- `Recipe` (the how-to-make section, with required fields)
- `BreadcrumbList`
- `Person` (author = Lewis Vaughan, mirroring TableJourney's pattern)
- `Organization` + `WebSite` (sitewide, from base template)

Required `Recipe` fields per Google's rich-result spec:
- name, image, recipeIngredient (≥1), recipeInstructions (≥1)
- author (Person), datePublished
- recipeCuisine, recipeCategory
- recipeYield, totalTime (ISO-8601 PT format)
- nutrition (optional but recommended)

Required `Article` fields:
- headline, datePublished, dateModified
- author (Person), publisher (Organization)
- image (real URL, not relative)
- inLanguage: "en"
- mainEntityOfPage

## 2. No duplicate JSON-LD properties

Google rejects ANY duplicate property (even when values match) with
"Duplicate unique property. Items with this issue are invalid. Invalid
items are not eligible for Google Search's rich results." Caught
TableJourney 2026-06-07 on 18 pages because Round 10 template change
re-emitted `url` and `image`.

`check_jsonld.py` uses `object_pairs_hook` on every JSON-LD block to
surface duplicates BEFORE the parser collapses them. Run it after any
template change.

## 3. AI-tell phrase ban

These phrases are AI tells. NEVER emit in description / history / tip
prose:
- "hidden gem", "must-try", "world-class", "nestled in"
- "to die for", "iconic", "culinary journey", "second to none"
- "unparalleled", "a must visit", "wide selection"
- "renowned for", "boasts", "elevates", "showcases"

Replace with specific factual detail. "Sunday-only counter on Mott
Street since 1948" beats "iconic hidden gem."

## 4. No em-dash or en-dash

Hard ban across JSON, HTML, prose, comments. Em-dashes (—) and en-dashes
(–) are AI tells; humans use them inconsistently, AIs use them every
sentence. Also hyphen-with-spaces (" - ") used as em-dash substitute is
banned.

## 5. URL hygiene

- All source URLs use `https://` (never `http://`)
- No Wikipedia URLs as the primary `source_url` for the dish (Wikipedia
  is OK as a secondary reference but not as provenance)
- No discovery directories (Yelp, TripAdvisor, Michelin Guide directory
  links) as the `where_to_eat` URLs — link to actual operator sites or
  to the corresponding TableJourney venue page

## 6. Cuisine + category taxonomy

`cuisine` field uses Title Case ("Italian", not "italian"). One value
per dish — no "Italian/French" hybrid declarations. Canonical cuisines
list lives in `site-data/cuisines/_taxonomy.json` (build before first
ship).

`category` field uses lowercase single-word: "pasta", "soup", "salad",
"bread", "dessert", "rice", "stew", "noodle", "sandwich", "pastry",
"beverage", "cocktail", "appetizer".

## 7. Editorial score

`editorial_score` is the orchestrator's verdict on a 1.0 to 4.9 scale.
4.9 = canonical, definitive. 4.0 = strong recommendation. 3.0 = included
because the cuisine guide would feel incomplete without it. Never 5.0.

## 8. verified block (provenance is mandatory)

```json
{
  "verified": {
    "source_url": "https://operator.com/recipe",
    "history_evidence_url": "https://...",
    "checked_on": "2026-06-07"
  }
}
```

No verified block = no publish. Same rule as TableJourney.

## 9. Page-level meta

- `<title>` ≤ 65 chars, ends with " | WorldDishAtlas"
- `<meta description>` 120-160 chars, unique site-wide
- Canonical tag self-referencing
- Open Graph: type=article for dish/cuisine/ingredient/comparison pages;
  type=website for home + chrome
- Twitter card: summary_large_image
- `<meta name=robots>` index,follow with max-image-preview:large

## 10. Visible signals

Every dish page renders:
- "Last verified [YYYY-MM-DD]" (from verified.checked_on)
- "Edited by Lewis Vaughan" (links to /about/lewis/)
- Reading time estimate
- A clear "Where to eat this dish" section linking to TableJourney venue
  pages (cross-site link equity flow)

## 11. Internal linking concentration

Homepage links to:
- Top 50 most-popular dishes (by editorial_score + cross-cuisine
  popularity)
- Top 30 cuisines
- Top 20 ingredients
- Comparison pages featured on each cuisine hub

Every dish page links to:
- Its cuisine page
- 3-5 "related dishes" (within cuisine or by ingredient overlap)
- Where to eat (TableJourney venue pages)
- Ingredient pages for its core ingredients
- 1-2 comparison pages ("X vs Y") where relevant

## 12. Image discipline

- Self-host all hero images at `/img/dish-<slug>.jpg` (max 800px on long
  side, 80-90% quality JPEG, ~50KB)
- Every hero img has explicit width + height (CLS prevention)
- Hero img has fetchpriority="high"
- Below-fold imgs have loading="lazy"
- Every img has alt text (specific, not generic — "Spaghetti carbonara
  with crispy guanciale on white plate" not "image")

## 13. Cross-site signals

WorldDishAtlas IS NOT a TableJourney clone. They cross-reference each
other through:
- Dish pages link to TableJourney venue pages in "where to eat" section
- TableJourney signature-dish entries can link to WorldDishAtlas dish
  pages for the full "what is X" treatment
- Same Person schema (Lewis Vaughan) so Google sees same expert across
  both
- Both sites in the same Organization graph (TableJourney parent)
