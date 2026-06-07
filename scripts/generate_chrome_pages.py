#!/usr/bin/env python3
"""Generate WorldDishAtlas chrome pages: about, lewis, methodology,
contact, privacy, terms, cookies, disclaimer.

Mirrors the TableJourney chrome generator pattern. All pages share the
chrome/page.html template; per-page body lives in dedicated functions
below. Person JSON-LD is emitted on /about/lewis/ to anchor the
named-author E-E-A-T signal.
"""

import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
TEMPLATES = REPO / "templates"
BASE = "https://worlddishatlas.com"


def crumb(*pairs):
    return [{"name": n, "url": u} for n, u in pairs]


def _about_html():
    return """
<p>WorldDishAtlas is a global encyclopedia of dishes. For every plate
worth eating, we write the canonical version: what is it, where did it
come from, how do you make it, and where do you eat the best one.</p>

<p>We are the what-is-this-dish layer to <a href="https://tablejourney.com"
rel="noopener">TableJourney</a>'s where-to-eat layer. Where TableJourney
sends you to the right restaurant, WorldDishAtlas tells you what to
order when you get there.</p>

<h2>How a dish gets covered</h2>
<p>Every dish page on this site is written by one editor working from a
shared brief that requires: a verified primary source for the canonical
recipe, a documented history with a cited source, and a venue list of
where to eat the dish in the wild. Every page is then human-reviewed by
the editor of record before it ships.</p>

<p>The verified date you see at the bottom of each dish page is the day
the editor last cross-checked that record against its primary source.
The full pipeline is on the <a href="/methodology/">methodology page</a>.</p>

<h2>What we will not publish</h2>
<ul>
  <li>A recipe without a documented primary source.</li>
  <li>A dish history sourced only from Wikipedia.</li>
  <li>A where-to-eat recommendation we cannot trace to a real venue at
    a current address.</li>
  <li>Copy that reads like AI slop. We have a banned-phrase list and we
    enforce it.</li>
</ul>

<h2>Contact</h2>
<p>Press, corrections, partnership inquiries and tips on what we
should cover next go through the <a href="/contact/">contact page</a>.</p>
"""


def _lewis_html():
    li = os.environ.get("TJ_LEWIS_LINKEDIN_URL")
    gh = os.environ.get("TJ_LEWIS_GITHUB_URL", "https://github.com/lewismvaughan")
    links = []
    if li:
        links.append(f'<a href="{li}" rel="me noopener" target="_blank">LinkedIn</a>')
    if gh:
        links.append(f'<a href="{gh}" rel="me noopener" target="_blank">GitHub</a>')
    social = ""
    if links:
        joined = " and ".join(links) if len(links) <= 2 else ", ".join(links[:-1]) + ", and " + links[-1]
        social = f'<p>Find Lewis on {joined}.</p>'
    return f"""
<figure class="wda-author-photo">
  <img src="/img/lewis.jpg" alt="Lewis Vaughan, founder and editor of WorldDishAtlas" width="200" height="356" loading="eager">
</figure>

<p>Lewis Vaughan is the founder and editor of WorldDishAtlas.</p>

<h2>Background</h2>
<p>Lewis is based in the United Kingdom. He is also the founder of
<strong>Rowie POS</strong>, a point-of-sale system used by restaurants,
and the founder and editor of <a href="https://tablejourney.com"
rel="noopener">TableJourney</a>. Working with restaurant operators
day-to-day gives him a direct line into the economics behind a tasting
menu, why a Tuesday night service is softer than a Friday one, and which
neighborhoods are actually worth walking to for a specific dish.</p>

<p>WorldDishAtlas was built to write about dishes the way restaurants
talk about them on a service line: one dish, one canonical version, one
specific way to do it right.</p>

<h2>What he edits</h2>
<p>Every dish published on WorldDishAtlas is read end-to-end by Lewis
before it ships. He catches what automated checks miss: a wrong
attribution, a tone issue, a step that does not survive a real
kitchen, a recipe that does not match the canonical regional version.
The verified date on each dish page is the day Lewis last cross-checked
that record against its primary source.</p>

<h2>Honest about how this gets made</h2>
<p>WorldDishAtlas uses AI tools for research synthesis, copy edits and
source-URL checks. No page is published as raw AI output. Every factual
claim is cross-checked by a named human editor against a primary source,
and the source is saved into the dish record. Lewis signs off on every
dish.</p>

<h2>Get in touch</h2>
<p>The <a href="/contact/">contact page</a> is the way. Press inquiries,
corrections, partnership ideas and recommendations all go through there.
Lewis reads every email.</p>

{social}
"""


def _methodology_html():
    return """
<p>How WorldDishAtlas decides what to publish, and how we know it is
still true on the day you read it.</p>

<h2>Every dish is verified</h2>
<p>Every dish we publish carries a verification record. We save the
source we cited for the canonical recipe, the source we cited for the
dish's history, and the date a human editor last cross-checked both. If
a dish does not have that record, it does not get published.</p>

<p>The date the editor last verified the entry is shown on every dish
page as "Last verified." It is set by a human, not auto-stamped.</p>

<h2>One human editor signs off</h2>
<p>Every dish is read end-to-end and signed off by <a
href="/about/lewis/">Lewis Vaughan</a> before it goes live. AI tools
help with research synthesis, copy edits and source-URL checks; no page
is published as raw AI output. Every factual claim is cross-checked
against a primary source.</p>

<h2>What we will not publish</h2>
<ul>
  <li>A dish without a verified primary source for the canonical recipe.</li>
  <li>A dish whose history is sourced only from Wikipedia. Wikipedia is
    fine as a secondary reference; it is not enough as the only one.</li>
  <li>A where-to-eat recommendation that points to a closed venue or to
    a directory listing instead of an operator page.</li>
  <li>Copy with AI tells. We have a banned-phrase list (hidden gem,
    must-try, world-class, nestled in, and the rest) and we enforce it
    in CI before any page ships.</li>
</ul>

<h2>Weekly drift check</h2>
<p>Every Sunday we re-probe every source URL on the site for drift.
Sites go dead. Recipes change. When we find a change, it gets fixed
that week and the affected pages get a fresh verification stamp.</p>

<h2>Editorial scoring</h2>
<p>The number next to each dish is our editorial verdict on its
canonical-ness, on a 1.0 to 4.9 scale. A 4.9 means definitive. A 3.0
means included because the cuisine guide would feel incomplete without
it.</p>

<h2>Corrections</h2>
<p>If a recipe has drifted, an attribution is wrong, or a venue has
moved, the <a href="/contact/">contact page</a> is the way. Material
corrections are called out at the bottom of the affected page.</p>
"""


def _contact_html():
    return """
<p>The fastest way to reach the WorldDishAtlas editorial desk is email.</p>

<h2>Editorial</h2>
<p>For corrections, story tips, dishes you think we should cover, or
recommendations on where the canonical version of a dish lives, email
<strong>hello@worlddishatlas.com</strong>.</p>

<h2>Press and partnerships</h2>
<p>For press inquiries, partnership ideas, or to syndicate any of our
dish guides, email <strong>press@worlddishatlas.com</strong>.</p>

<h2>Lewis</h2>
<p>For anything else, the editor reads every email. See <a
href="/about/lewis/">about Lewis</a> for context.</p>
"""


def _privacy_html():
    return """
<p>WorldDishAtlas does not require an account. We do not run user logins,
comments, profiles, or any other identity-bearing feature on this site.
What we collect is limited, and we explain it here.</p>

<h2>What we collect</h2>
<ul>
  <li><strong>Analytics</strong>: Google Tag Manager + Microsoft Clarity
    record anonymized page views, session recordings and heatmaps so we
    can understand which dishes readers actually use the site for. No
    personally identifying information is captured.</li>
  <li><strong>Server access logs</strong>: standard web-server logs
    (IP, user-agent, requested URL, timestamp) are retained for 30
    days for security and abuse-handling purposes.</li>
</ul>

<h2>What we do not do</h2>
<ul>
  <li>We do not sell or rent any data we collect.</li>
  <li>We do not run user accounts or store passwords.</li>
  <li>We do not display third-party advertising on the site at this time.</li>
</ul>

<h2>Cookies</h2>
<p>The analytics tools listed above set their own cookies. Full cookie
detail is on the <a href="/cookies/">cookies page</a>. Your browser's
do-not-track setting is respected.</p>

<h2>Contact</h2>
<p>Privacy questions: email <strong>privacy@worlddishatlas.com</strong>
or use the <a href="/contact/">contact page</a>.</p>
"""


def _terms_html():
    return """
<p>WorldDishAtlas is an editorial publication. By using this site you
agree to the following.</p>

<h2>1. Content is editorial, not legal or medical advice</h2>
<p>The recipes, histories, and where-to-eat recommendations on this site
are editorial. They are not professional culinary, dietary, medical, or
legal advice. If you have a food allergy, an intolerance, or a medical
restriction, consult a qualified professional.</p>

<h2>2. Use at your own risk</h2>
<p>Recipes are tested by the editor but not in your kitchen. Cooking
involves heat, sharp tools, and raw ingredients. You are responsible for
your own kitchen safety.</p>

<h2>3. Affiliate links</h2>
<p>Some links on this site may be affiliate links. Affiliate revenue
plays no part in editorial selection. If a venue or product is bad, it
gets that verdict and the affiliate link goes away.</p>

<h2>4. Copyright</h2>
<p>All editorial content on this site, including dish histories,
recipes, and photography, is copyright WorldDishAtlas. Quote freely with
attribution; do not republish wholesale without written permission.</p>

<h2>5. Changes</h2>
<p>We may update these terms occasionally. Material changes will be
called out on the home page.</p>
"""


def _cookies_html():
    return """
<p>What cookies WorldDishAtlas sets, and why.</p>
<h2>Analytics</h2>
<p>Google Tag Manager and Microsoft Clarity each set their own cookies
to measure page views, sessions and on-page behaviour. These are
anonymized.</p>
<h2>No advertising cookies</h2>
<p>We do not run third-party advertising at this time, so no advertising
cookies are set.</p>
<h2>Control</h2>
<p>Use your browser's cookie controls to clear or block cookies. Most
of the site works without them.</p>
"""


def _disclaimer_html():
    return """
<p>WorldDishAtlas publishes editorial dish guides, recipes, and venue
recommendations. We are not a medical, dietary, legal, or financial
service. The content on this site is for general information and
editorial purposes only.</p>
<p>If you have a food allergy, medical condition, or other restriction
that affects what you can eat, consult a qualified professional rather
than relying on this site.</p>
"""


PAGES = [
    {"slug": "about", "title": "About WorldDishAtlas", "subtitle": "A global dish encyclopedia, edited by humans.",
     "meta_description": "WorldDishAtlas is a global dish encyclopedia. Canonical recipes, dish histories, and where to eat them. Edited by humans, AI-assisted research, fully verified.",
     "page_type": "about", "body": _about_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("About", None))},
    {"slug": "about/lewis", "title": "Lewis Vaughan, founder and editor of WorldDishAtlas",
     "subtitle": "Founder and editor of WorldDishAtlas.",
     "meta_description": "Lewis Vaughan, founder and editor of WorldDishAtlas. UK-based, founder of Rowie POS and TableJourney. Edits every dish before publish; honest about AI assistance.",
     "page_type": "about", "body": _lewis_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("About", f"{BASE}/about/"), ("Lewis Vaughan", None)),
     "schema_person": {
        "name": "Lewis Vaughan", "url": f"{BASE}/about/lewis/",
        "image": f"{BASE}/img/lewis.jpg",
        "jobTitle": "Founder and editor",
        "worksFor": {"@type": "Organization", "name": "WorldDishAtlas", "url": f"{BASE}/"},
        "sameAs": [u for u in [os.environ.get("TJ_LEWIS_LINKEDIN_URL"),
                                os.environ.get("TJ_LEWIS_GITHUB_URL", "https://github.com/lewismvaughan")] if u]}},
    {"slug": "methodology", "title": "Methodology — how every WorldDishAtlas claim gets verified",
     "subtitle": "How we know what we know.",
     "meta_description": "How WorldDishAtlas verifies every claim before publishing. Verified primary sources on every dish, weekly drift check, single human editor of record.",
     "page_type": "webpage", "body": _methodology_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Methodology", None))},
    {"slug": "contact", "title": "Contact WorldDishAtlas",
     "subtitle": "Email is the fastest way.",
     "meta_description": "Contact the WorldDishAtlas editorial desk. Press, corrections, story tips, partnership inquiries, and dish recommendations all go through here.",
     "page_type": "contact", "body": _contact_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Contact", None))},
    {"slug": "privacy", "title": "Privacy",
     "subtitle": "What we collect, what we do not, and why.",
     "meta_description": "WorldDishAtlas privacy policy. No user accounts; anonymized analytics only; standard server logs retained 30 days; no advertising cookies.",
     "page_type": "webpage", "body": _privacy_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Privacy", None))},
    {"slug": "terms", "title": "Terms",
     "subtitle": "The ground rules.",
     "meta_description": "WorldDishAtlas terms of use. Editorial content, not legal or medical advice. Use at your own risk. Copyright and affiliate disclosures.",
     "page_type": "webpage", "body": _terms_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Terms", None))},
    {"slug": "cookies", "title": "Cookies",
     "subtitle": "What cookies we set, and why.",
     "meta_description": "WorldDishAtlas cookies. Analytics only; no advertising cookies; respect your browser controls.",
     "page_type": "webpage", "body": _cookies_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Cookies", None))},
    {"slug": "disclaimer", "title": "Disclaimer",
     "subtitle": "General information, not professional advice.",
     "meta_description": "WorldDishAtlas disclaimer. Content is editorial; not medical, dietary, legal, or financial advice. Consult a professional for restrictions.",
     "page_type": "webpage", "body": _disclaimer_html(),
     "breadcrumb": crumb(("Home", f"{BASE}/"), ("Disclaimer", None))},
]


def render_page(env, spec):
    canonical = f"{BASE}/{spec['slug']}/"
    page_ctx = {
        "title": f"{spec['title']} | WorldDishAtlas",
        "meta_description": spec["meta_description"],
        "canonical_url": canonical,
        "h1": spec["title"],
        "subtitle": spec.get("subtitle", ""),
        "body_html": spec["body"],
        "breadcrumb_items": spec["breadcrumb"],
        "page_type": spec["page_type"],
        "og_image": f"{BASE}/img/og-default.jpg",
        "og_type": "website",
        "schema_person": spec.get("schema_person"),
    }
    template = env.get_template("chrome/page.html")
    html = template.render(page=page_ctx)
    out = CONTENT / spec["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html"]))
    for spec in PAGES:
        out = render_page(env, spec)
        print(f"  wrote {out.relative_to(REPO)}")
    print(f"\nDONE. {len(PAGES)} chrome pages rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
