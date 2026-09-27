#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NEW_FOOTER = (
    '<footer><div class="container"><div>'
    '<a href="/">Home</a>'
    '<a href="/how-it-works/">How It Works</a>'
    '<a href="/about/">About</a>'
    '<a href="/contact/">Contact</a>'
    '<a href="/privacy/">Privacy</a>'
    '<a href="/terms/">Terms</a>'
    '</div><div>© 2026 DevSecSuite.</div></div></footer>'
)

FOOTER_REGEX = re.compile(r'<footer>.*?</footer>', re.DOTALL)


def patch(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  SKIP {path.name}: {e}")
        return None

    if "<footer>" not in content:
        return "no-footer"

    # Already up to date?
    if 'href="/how-it-works/"' in content and content.count("<footer>") >= 1:
        # Might still have old footer without how-it-works in the footer specifically
        # Let's check if the footer block contains the link
        match = FOOTER_REGEX.search(content)
        if match and 'href="/how-it-works/"' in match.group(0):
            return "already"

    new_content, count = FOOTER_REGEX.subn(NEW_FOOTER, content)

    if count == 0:
        return "no-footer"

    if new_content == content:
        return "already"

    path.write_text(new_content, encoding="utf-8")
    return "patched"


def main():
    patched = []
    skipped = []
    no_footer = []

    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        result = patch(p)
        rel = p.relative_to(ROOT)
        if result == "patched":
            patched.append(rel)
        elif result == "already":
            skipped.append(rel)
        elif result == "no-footer":
            no_footer.append(rel)
        else:
            print(f"  ERROR {rel}: {result}")

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f in patched:
        print(f"  ✓ {f}")

    print(f"\n=== ALREADY UP TO DATE ({len(skipped)}) ===")
    for f in skipped:
        print(f"  - {f}")

    print(f"\n=== NO FOOTER FOUND ({len(no_footer)}) ===")
    for f in no_footer:
        print(f"  ! {f}")


if __name__ == "__main__":
    main()
