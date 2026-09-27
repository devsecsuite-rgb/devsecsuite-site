#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = '<a href="/how-it-works/">How It Works</a>'


def patch_file(path):
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  SKIP {path.name}: {e}")
        return False

    # Find the first <nav>...</nav> block
    nav_match = re.search(r'<nav[^>]*>(.*?)</nav>', content, re.DOTALL)
    if not nav_match:
        return False

    # Already has the link?
    if '/how-it-works/' in nav_match.group(1):
        return False

    # Insert the link right after the opening <nav> tag
    new_content = re.sub(
        r'(<nav[^>]*>)',
        rf'\1{LINK}',
        content,
        count=1
    )

    if new_content == content:
        return False

    path.write_text(new_content, encoding='utf-8')
    return True


def main():
    changed = []
    skipped = []

    for p in sorted(ROOT.rglob('*.html')):
        if '.git' in p.parts:
            continue
        if patch_file(p):
            changed.append(p.relative_to(ROOT))
        else:
            skipped.append(p.relative_to(ROOT))

    print(f"\n=== PATCHED {len(changed)} FILES ===")
    for c in changed:
        print(f"  ✓ {c}")

    print(f"\n=== SKIPPED {len(skipped)} FILES (already patched or no <nav>) ===")
    for s in skipped:
        print(f"  - {s}")


if __name__ == '__main__':
    main()
