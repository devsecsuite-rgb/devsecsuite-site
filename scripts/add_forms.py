#!/usr/bin/env python3
"""
Add a newsletter form to any devsecsuite page that doesn't have one.
Inserts the form right before the footer.
"""
import os
import re

NEW_UUID = "d540b73c-53d0-46a3-8692-3827aedc2d77"

SKIP = {"scripts", ".github", "about", "contact", "privacy", "terms", "thank-you", "node_modules"}

FORM_BLOCK = '''
<section class="content-section" style="text-align:center">
<h2 style="margin-top:0">Get Developer Tips Weekly</h2>
<p>Free tips on developer tools, browser APIs, and modern web workflows. No spam. Unsubscribe anytime.</p>
<form action="https://api.web3forms.com/submit" method="POST" style="max-width:400px;margin:1rem auto 0">
    <input type="hidden" name="access_key" value="{UUID}">
    <input type="email" name="email" required placeholder="your@email.com" style="width:100%;padding:.75rem;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#e6e6e6;font-size:1rem;margin-bottom:.5rem">
    <input type="hidden" name="tool" value="{NAME}">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="subject" value="DevSecSuite subscriber — {NAME}">
    <input type="hidden" name="redirect" value="https://devsecsuite.com/thank-you/">
    <button type="submit" style="width:100%;background:#238636;color:#fff;padding:.75rem;border:none;border-radius:6px;font-weight:600;cursor:pointer">Subscribe</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>
</section>
'''


def get_name(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "DevSecSuite Tool"


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    if "api.web3forms.com" in html:
        print(f"  Already has form: {path}")
        return False

    if "</main>" not in html:
        print(f"  No </main>: {path}")
        return False

    name = get_name(html)
    block = FORM_BLOCK.replace("{UUID}", NEW_UUID).replace("{NAME}", name)
    html = html.replace("</main>", block + "\n</main>", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Added form: {path}")
    return True


def main():
    added = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file == "index.html":
                path = os.path.join(root, file)
                if path == "./index.html":
                    continue
                if patch(path):
                    added += 1
    print(f"\nDone. Added: {added}")


if __name__ == "__main__":
    main()
