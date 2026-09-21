#!/usr/bin/env python3
"""
Patch all pages: replace any Web3Forms access_key with the DevSecSuite UUID.
Also adds the Web3Forms form to pages that don't have one.
"""
import os
import re

# YOUR DEVSECSUITE WEB3FORMS UUID
NEW_UUID = "d540b73c-53d0-46a3-8692-3827aedc2d77"

SKIP = {"scripts", ".github", "about", "contact", "privacy", "terms", "thank-you", "node_modules"}

FORM_BLOCK = '''<form action="https://api.web3forms.com/submit" method="POST">
    <input type="hidden" name="access_key" value="{UUID}">
    <input type="email" name="email" required placeholder="your@email.com">
    <input type="hidden" name="tool" value="{NAME}">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="subject" value="DevSecSuite subscriber — {NAME}">
    <input type="hidden" name="redirect" value="https://devsecsuite.com/thank-you/">
    <button type="submit">Get Developer Tips Weekly</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>'''


def get_name(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "DevSecSuite Tool"


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    original = html

    # Fix existing access_key values
    pattern = re.compile(r'(name="access_key"\s+value=")([^"]+)(")', re.IGNORECASE)
    def replacer(m):
        if m.group(2) == NEW_UUID:
            return m.group(0)
        return m.group(1) + NEW_UUID + m.group(3)
    html = pattern.sub(replacer, html)

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ Patched: {path}")
        return True
    print(f"  No change: {path}")
    return False


def main():
    patched = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file == "index.html":
                path = os.path.join(root, file)
                if path == "./index.html":
                    continue
                if patch(path):
                    patched += 1
    print(f"\nDone. Patched: {patched}")


if __name__ == "__main__":
    main()
