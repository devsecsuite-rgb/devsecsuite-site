#!/usr/bin/env python3
"""
One-time patch: add missing viewport meta and OG tags to all HTML pages.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://devsecsuite.com"
OG_IMAGE = f"{BASE_URL}/og-image.png"

VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

# Patterns
HEAD_CLOSE = re.compile(r'</head>', re.IGNORECASE)
VIEWPORT_PATTERN = re.compile(r'<meta\s+name=["\']viewport["\']', re.IGNORECASE)
TITLE_PATTERN = re.compile(r'<title>([^<]+)</title>', re.IGNORECASE)
DESC_PATTERN = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', re.IGNORECASE)
CANONICAL_PATTERN = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.IGNORECASE)
OG_TITLE_PATTERN = re.compile(r'<meta\s+property=["\']og:title["\']', re.IGNORECASE)


def slug_to_url(path):
    """Derive URL from file path."""
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if len(parts) == 1:
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{parts[0]}/"


def build_og_block(title, desc, url):
    title = title.replace('"', '&quot;')
    desc = desc.replace('"', '&quot;')
    lines = [
        f'<meta property="og:type" content="website">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
    ]
    return "\n".join(lines)


def patch(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: {e}"

    original = content
    changes = []

    # Extract title + description
    title_match = TITLE_PATTERN.search(content)
    desc_match = DESC_PATTERN.search(content)
    canonical_match = CANONICAL_PATTERN.search(content)

    title = title_match.group(1).strip() if title_match else "DevSecSuite"
    desc = desc_match.group(1).strip() if desc_match else "Free browser-based developer and security tools."
    url = canonical_match.group(1).strip() if canonical_match else slug_to_url(path)

    # 1. Add viewport if missing
    if not VIEWPORT_PATTERN.search(content):
        # Insert after <meta charset="UTF-8">
        charset_match = re.search(r'<meta\s+charset=["\']UTF-8["\'][^>]*>', content, re.IGNORECASE)
        if charset_match:
            content = content[:charset_match.end()] + "\n" + VIEWPORT + content[charset_match.end():]
        else:
            # Fallback: insert right after <head>
            head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
            if head_match:
                content = content[:head_match.end()] + "\n" + VIEWPORT + content[head_match.end():]
        changes.append("added viewport meta")

    # 2. Add OG tags if missing
    if not OG_TITLE_PATTERN.search(content):
        og_block = build_og_block(title, desc, url)
        head_close = HEAD_CLOSE.search(content)
        if head_close:
            content = content[:head_close.start()] + og_block + "\n" + content[head_close.start():]
            changes.append("added OG + Twitter tags")

    if content != original:
        path.write_text(content, encoding="utf-8")
        return changes
    return None


def main():
    patched = []
    skipped = []

    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        result = patch(p)
        rel = p.relative_to(ROOT)
        if result is None:
            skipped.append(rel)
        elif isinstance(result, str) and result.startswith("error"):
            print(f"  ERROR {rel}: {result}")
        else:
            patched.append((rel, result))

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f, changes in patched:
        print(f"  ✓ {f}")
        for c in changes:
            print(f"      - {c}")

    print(f"\n=== SKIPPED {len(skipped)} FILES (already have tags) ===")
    for f in skipped[:10]:
        print(f"  - {f}")
    if len(skipped) > 10:
        print(f"  ... and {len(skipped) - 10} more")


if __name__ == "__main__":
    main()
