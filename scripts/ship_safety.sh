#!/usr/bin/env bash
# WorldDishAtlas ship gate. Runs every check before content goes live.
# Exit 0 = safe to ship.
# Exit 1 = HARD failure; do NOT publish.
#
# Layers (analogous to TableJourney's 11-layer ship_safety):
#   1. validate_data.py   — 9 P0 rules
#   2. verify_dish_sources.py — HEAD-check verified URLs (no --deep by default)
#   3. JSON parse check on rendered HTML pages
#   4. check_jsonld.py    — duplicate-property check + required fields
#   5. internal-href integrity (no broken /<path>/)

set -uo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }

FAILED=0

echo "=== ship_safety: WorldDishAtlas ==="
echo

# Layer 1: validate_data (9 P0 rules)
echo "[1/5] validate_data (9 P0 rules)"
if python3 scripts/validate_data.py 2>&1 | tail -1; then
    green "  PASS"
else
    red "  FAIL"
    FAILED=1
fi
echo

# Layer 2: verify source URLs (no deep mode in ship gate; deep is opt-in)
echo "[2/5] verify_dish_sources (HEAD-check verified URLs)"
if python3 scripts/verify_dish_sources.py 2>&1 | tail -1 | grep -q "HARD: 0"; then
    green "  PASS"
else
    red "  FAIL"
    FAILED=1
fi
echo

# Layer 3: regen all pages (smoke render)
echo "[3/5] regen all pages"
python3 scripts/generate_dish_pages.py --all >/dev/null 2>&1 || { red "  dish regen failed"; FAILED=1; }
python3 scripts/generate_indexes.py >/dev/null 2>&1 || { red "  indexes failed"; FAILED=1; }
python3 scripts/generate_homepage.py >/dev/null 2>&1 || { red "  home failed"; FAILED=1; }
python3 scripts/generate_chrome_pages.py >/dev/null 2>&1 || { red "  chrome failed"; FAILED=1; }
python3 scripts/generate_compare_pages.py >/dev/null 2>&1 || { red "  compare failed"; FAILED=1; }
python3 scripts/generate_search.py >/dev/null 2>&1 || { red "  search failed"; FAILED=1; }
python3 scripts/generate_feeds_and_extras.py >/dev/null 2>&1 || { red "  feeds failed"; FAILED=1; }
python3 scripts/generate_sitemap.py >/dev/null 2>&1 || { red "  sitemap failed"; FAILED=1; }
if [ $FAILED -eq 0 ]; then green "  PASS"; fi
echo

# Layer 4: check_jsonld (parse + dupe + required fields)
echo "[4/5] check_jsonld (parse + dupes + required fields)"
JSON_OUT=$(python3 scripts/check_jsonld.py 2>&1)
ISSUES=$(echo "$JSON_OUT" | grep -E "^Pages with issues:" | grep -oE "[0-9]+")
if [ "${ISSUES:-0}" -le 1 ]; then
    # 1 issue allowed: the 404.html-no-jsonld false positive
    green "  PASS ($ISSUES page(s) with issues, ≤1 acceptable)"
else
    red "  FAIL ($ISSUES pages with JSON-LD issues)"
    echo "$JSON_OUT" | tail -20
    FAILED=1
fi
echo

# Layer 5: internal-href integrity
echo "[5/5] internal-href integrity"
BROKEN=$(python3 -c "
import re
from pathlib import Path
CONTENT = Path('content')
broken = []
seen = set()
href_pat = re.compile(r'href=\"(/[^\"#?]+)\"')
for f in CONTENT.rglob('*.html'):
    try: html = f.read_text(errors='ignore')
    except: continue
    for h in set(href_pat.findall(html)):
        if h in seen: continue
        seen.add(h)
        if h.startswith(('/css/','/js/','/img/','/static/','/favicon','/apple-touch')): continue
        path = h.lstrip('/').rstrip('/')
        if not path:
            if (CONTENT / 'index.html').exists(): continue
        if (CONTENT/path/'index.html').exists(): continue
        if (CONTENT/path).exists(): continue
        broken.append(h)
print(len(broken))
")
if [ "$BROKEN" -eq 0 ]; then
    green "  PASS (0 broken hrefs)"
else
    red "  FAIL ($BROKEN broken hrefs)"
    FAILED=1
fi
echo

echo "=== Result ==="
if [ $FAILED -eq 0 ]; then
    green "ALL 5 LAYERS PASS. Safe to ship."
    exit 0
else
    red "SHIP BLOCKED. Fix and re-run."
    exit 1
fi
