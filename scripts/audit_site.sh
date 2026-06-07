#!/usr/bin/env bash
# Weekly drift audit cron. Probes source URLs for rot, verifies content
# integrity, reports anything that needs the editor's attention.
# Schedule: Sunday 06:00 UTC via cron.

set -uo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
LOG="/home/lewis/wda-audit.log"

{
    echo "=== WDA weekly drift audit — $(date -u +'%Y-%m-%d %H:%M UTC') ==="
    echo
    echo "[1] verify_dish_sources (HEAD + deep content check)"
    python3 scripts/verify_dish_sources.py --deep 2>&1 | tail -10
    echo
    echo "[2] check_jsonld"
    python3 scripts/check_jsonld.py 2>&1 | tail -10
    echo
    echo "[3] sitemap parity"
    python3 -c "
import re
from pathlib import Path
sm = Path('content/sitemap-pages.xml')
if sm.exists():
    urls = re.findall(r'<loc>([^<]+)</loc>', sm.read_text())
    miss = 0
    for u in urls:
        p = u.replace('https://worlddishatlas.com/','').rstrip('/')
        f = Path('content') / (p or '.') / 'index.html'
        if not f.exists() and not (Path('content') / p).exists(): miss += 1
    print(f'  sitemap URLs: {len(urls)}, missing on disk: {miss}')
"
    echo
    echo "=== END ==="
    echo
} >> "$LOG" 2>&1

echo "Audit appended to $LOG"
