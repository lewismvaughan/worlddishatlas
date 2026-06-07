# WorldDishAtlas — dish data schema

Every dish lives in `site-data/dishes/<slug>.json`. The slug is the URL
path: `worlddishatlas.com/dish/<slug>/`.

## Required fields (validate_data.py hard-fails)

```json
{
  "slug": "carbonara",
  "name": "Carbonara",
  "name_native": "Spaghetti alla carbonara",
  "cuisine": "Italian",
  "category": "pasta",
  "region": "Lazio",
  "country": "Italy",
  "description": "120-160 char meta-description-friendly intro.",
  "history": "200-600 word history of the dish. No AI tells.",
  "ingredients_summary": "Eggs, guanciale, pecorino romano, black pepper, pasta.",
  "ingredients": [
    {"name": "Spaghetti", "amount": "400g"},
    {"name": "Guanciale", "amount": "150g, diced"},
    {"name": "Pecorino Romano", "amount": "100g, finely grated"},
    {"name": "Egg yolks", "amount": "4 large"},
    {"name": "Black pepper", "amount": "to taste, fresh-cracked"}
  ],
  "method": [
    "Step 1...",
    "Step 2..."
  ],
  "serves": 4,
  "prep_time": "PT15M",
  "cook_time": "PT15M",
  "total_time": "PT30M",
  "verified": {
    "source_url": "https://operator-or-authoritative-source.com/recipe",
    "history_evidence_url": "https://historical-source.com/article",
    "checked_on": "2026-06-07"
  }
}
```

## Optional but high-impact fields

```json
{
  "variations": [
    {"name": "Roman style", "note": "Pecorino only, no parmesan"},
    {"name": "Tokyo carbonara", "note": "Often substitutes cream"}
  ],
  "where_to_eat": [
    {
      "name": "Da Felice a Testaccio",
      "city": "Rome",
      "country_slug": "italy",
      "city_slug": "rome",
      "tablejourney_url": "/italy/rome/restaurants/da-felice/"
    }
  ],
  "related_dishes": ["cacio-e-pepe", "amatriciana", "gricia"],
  "compared_to": ["cacio-e-pepe", "amatriciana"],
  "core_ingredients": ["egg", "guanciale", "pecorino-romano", "black-pepper"],
  "common_mistakes": [
    "Adding cream (the classic Roman recipe never uses cream)",
    "Using bacon instead of guanciale (changes the entire fat profile)"
  ],
  "tip": "Off the heat: temper the eggs into the pasta water before tossing.",
  "editorial_score": 4.8,
  "popularity_signal": "global",
  "dietary_notes": {
    "vegan_version": false,
    "gluten_free_version": false,
    "common_substitutions": []
  },
  "hero_image": "/img/dish-carbonara.jpg",
  "hero_image_alt": "Spaghetti carbonara with crispy guanciale, pecorino, and black pepper on a white plate",
  "hero_image_source_url": "https://unsplash.com/photos/...",
  "credits": [
    {"type": "michelin_associated", "venue": "...", "city": "Rome"}
  ]
}
```

## URL → file mapping

| URL | File |
|---|---|
| `/dish/carbonara/` | `site-data/dishes/carbonara.json` |
| `/cuisine/italian/` | aggregated from `cuisine: "Italian"` |
| `/cuisine/italian/carbonara/` | same dish, cuisine-scoped variant page |
| `/ingredient/guanciale/` | aggregated from `core_ingredients: [..., "guanciale"]` |
| `/compare/carbonara-vs-cacio-e-pepe/` | both dishes share `compared_to` |

## Schema.org emission (per page type)

### Dish page (`/dish/<slug>/`)

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Article",
      "@id": "https://worlddishatlas.com/dish/carbonara/#article",
      "headline": "Carbonara",
      "datePublished": "...",
      "dateModified": "...",
      "author": {
        "@type": "Person",
        "name": "Lewis Vaughan",
        "url": "https://worlddishatlas.com/about/lewis/"
      },
      "publisher": { "@type": "Organization", "name": "WorldDishAtlas" },
      "image": "...",
      "mainEntityOfPage": "...",
      "inLanguage": "en"
    },
    {
      "@type": "Recipe",
      "@id": "https://worlddishatlas.com/dish/carbonara/#recipe",
      "name": "Carbonara",
      "image": "...",
      "author": { "@type": "Person", "name": "Lewis Vaughan", ... },
      "datePublished": "...",
      "description": "...",
      "recipeCuisine": "Italian",
      "recipeCategory": "Pasta",
      "recipeYield": "4 servings",
      "prepTime": "PT15M",
      "cookTime": "PT15M",
      "totalTime": "PT30M",
      "recipeIngredient": ["400g spaghetti", "150g guanciale", ...],
      "recipeInstructions": [
        {"@type": "HowToStep", "text": "Step 1..."}
      ]
    },
    { "@type": "BreadcrumbList", ... }
  ]
}
```

### Cuisine page

Schema: `CollectionPage` + `BreadcrumbList` + `ItemList` (linking to
dishes within the cuisine).

### Ingredient page

Schema: `CollectionPage` + `BreadcrumbList` + `ItemList` (dishes using
the ingredient).

### Comparison page

Schema: `Article` + `BreadcrumbList`. Compares 2 dishes side-by-side.

## What we will NOT publish

- A dish entry without a `verified` block
- A dish whose `source_url` is a Wikipedia URL (Wikipedia is OK as
  secondary reference, not as provenance for the recipe)
- A recipe with fewer than 3 ingredients or fewer than 2 method steps
  (validate_data.py hard-fails — likely a stub, not a real recipe)
- A description with AI tells (see STANDARDS.md §3)
- A dish with `editorial_score >= 5.0`
- Any content containing em-dashes (—) or en-dashes (–)
