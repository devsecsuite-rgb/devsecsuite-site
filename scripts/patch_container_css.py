#!/usr/bin/env python3
"""
One-time patch: fix .header typo and add missing .container CSS rule.
Scans every HTML file in the repo.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The correct rules to ensure exist
CONTAINER_RULE = ".container{max-width:720px;margin:0 auto;padding:0 1.5rem}"
HEADER_CONTAINER_RULE = "header .container{display:flex;align-items:center;justify-content:space-between;max-width:960px}"

# What to look for
BROKEN_HEADER_RULE = re.compile(
    r'\.header\s+\.container\{[^}]*\}'
)
HAS_CONTAINER_RULE = re.compile(
    r'(?<!\.)(?<!header )(?<!footer )\.container\{[^}]*max-width[^}]*\}'
)


def patch_file(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  SKIP {path.name}: {e}")
        return "error"

    original = content
    changes = []

    # 1. Fix ".header .container" typo -> "header .container"
    if BROKEN_HEADER_RULE.search(content):
        content = BROKEN_HEADER_RULE.sub(HEADER_CONTAINER_RULE, content)
        changes.append("fixed .header typo")

    # 2. Add missing .container rule if absent
    if not HAS_CONTAINER_RULE.search(content):
        # Inject right after the header{...} rule
        header_match = re.search(r'(header\{[^}]*\})', content)
        if header_match:
            content = content[:header_match.end()] + "\n" + CONTAINER_RULE + content[header_match.end():]
            changes.append("added .container rule")
        else:
            changes.append("WARNING: no header{} block found to anchor")

    # 3. Ensure header .container exists (in case it was totally missing)
    if "header .container{" not in content:
        header_match = re.search(r'(header\{[^}]*\})', content)
        if header_match:
            content = content[:header_match.end()] + "\n" + HEADER_CONTAINER_RULE + content[header_match.end():]
            changes.append("added header .container rule")

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
        result = patch_file(p)
        rel = p.relative_to(ROOT)
        if result is None:
            skipped.append(rel)
        elif result == "error":
            pass
        else:
            patched.append((rel, result))

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f, changes in patched:
        print(f"  ✓ {f}")
        for c in changes:
            print(f"      - {c}")

    print(f"\n=== SKIPPED {len(skipped)} FILES (no changes needed) ===")
    # Only print first 10 to keep log short
    for f in skipped[:10]:
        print(f"  - {f}")
    if len(skipped) > 10:
        print(f"  ... and {len(skipped) - 10} more")


if __name__ == "__main__":
    main()
