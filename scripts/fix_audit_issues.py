#!/usr/bin/env python3
"""Fixes audit issues from 2026-11-16 SEO report."""
import re
import os
from bs4 import BeautifulSoup

SITE = "https://devsecsuite.com"
OG_IMAGE = f"{SITE}/og-image.png"

viewport_files = [
    "case-converter/index.html",
    "user-agent-parser/index.html",
]

og_files = [
    "all-tools/index.html",
    "url-parser/index.html",
    "http-status-codes/index.html",
    "mime-type-lookup/index.html",
    "htaccess-redirect-generator/index.html",
    "user-agent-parser/index.html",
    "cron-expression-builder/index.html",
    "uuid-bulk-generator/index.html",
    "random-number-generator/index.html",
    "lorem-ipsum-generator/index.html",
    "slug-generator/index.html",
    "case-converter/index.html",
    "how-it-works/index.html",
]

def add_viewport(html):
    if 'name="viewport"' in html:
        return html, False
    match = re.search(r'<meta charset="[^"]*">', html)
    if match:
        i = match.end()
        return html[:i] + '\n<meta name="viewport" content="width=device-width, initial-scale=1.0">' + html[i:], True
    match = re.search(r'<head[^>]*>', html)
    if match:
        i = match.end()
        return html[:i] + '\n<meta name="viewport" content="width=device-width, initial-scale=1.0">' + html[i:], True
    return html, False

def add_og_tags(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.find("title")
    title = title_el.text.strip().replace('"', '&quot;') if title_el else ""
    desc_el = soup.find("meta", attrs={"name": "description"})
    desc = (desc_el.get("content", "") if desc_el else "").replace('"', '&quot;')

    additions = []
    if not soup.find("meta", attrs={"property": "og:title"}):
        additions.append(f'<meta property="og:title" content="{title}">')
    if not soup.find("meta", attrs={"property": "og:description"}):
        additions.append(f'<meta property="og:description" content="{desc}">')
    if not soup.find("meta", attrs={"property": "og:image"}):
        additions.append(f'<meta property="og:image" content="{OG_IMAGE}">')
    if not soup.find("meta", attrs={"property": "og:url"}):
        additions.append(f'<meta property="og:url" content="{url}">')
    if not soup.find("meta", attrs={"property": "og:type"}):
        additions.append(f'<meta property="og:type" content="website">')

    if not additions:
        return html, 0
    block = "\n" + "\n".join(additions) + "\n"
    return html.replace("</head>", block + "</head>", 1), len(additions)

changes = []

for path in viewport_files:
    if not os.path.exists(path):
        print(f"SKIP (not found): {path}"); continue
    with open(path, "r", encoding="utf-8", newline="") as f:
        html = f.read()
    new, changed = add_viewport(html)
    if changed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print(f"✓ viewport added: {path}"); changes.append(path)
    else:
        print(f"= viewport ok: {path}")

for path in og_files:
    if not os.path.exists(path):
        print(f"SKIP (not found): {path}"); continue
    with open(path, "r", encoding="utf-8", newline="") as f:
        html = f.read()
    folder = os.path.dirname(path)
    url = f"{SITE}/{folder}/" if folder else f"{SITE}/"
    new, count = add_og_tags(html, url)
    if count:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print(f"✓ {count} OG tag(s) added: {path}"); changes.append(path)
    else:
        print(f"= OG tags ok: {path}")

print(f"\nTotal files changed: {len(changes)}")