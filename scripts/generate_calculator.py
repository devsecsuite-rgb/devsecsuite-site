#!/usr/bin/env python3
"""
DevSecSuite — Automated Developer Tool Generator
Multi-provider: Groq (primary) + OpenRouter (fallback).
"""
import os
import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# Load API keys from environment
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

if not GROQ_KEY and not OPENROUTER_KEY:
    print("ERROR: No API keys found. Set GROQ_API_KEY and/or OPENROUTER_API_KEY")
    sys.exit(1)

print(f"Groq key: {'set' if GROQ_KEY else 'missing'}")
print(f"OpenRouter key: {'set' if OPENROUTER_KEY else 'missing'}")

# Shared User-Agent (required — Cloudflare blocks default Python UA with error 1010)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Providers, tried in order
PROVIDERS = []
if GROQ_KEY:
    PROVIDERS.append({
        "name": "groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": GROQ_KEY,
        "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
    })
if OPENROUTER_KEY:
    PROVIDERS.append({
        "name": "openrouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": OPENROUTER_KEY,
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
        ],
    })

QUEUE_FILE = "scripts/queue.json"
TIMEOUT_PER_ATTEMPT = 120
MAX_RETRIES = 2


def load_queue():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_next(queue):
    for i, item in enumerate(queue):
        if item.get("status") != "done":
            return i, item
    return None, None


def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)


def build_prompt(item):
    return f"""You are an expert web developer and technical writer.

Generate a complete single-file HTML page for a developer tool with these specs:

- Tool name: {item['name']}
- Slug: {item['slug']}
- Purpose: {item['description']}
- Inputs: {item['inputs']}
- Formula/logic: {item['formula']}

REQUIREMENTS:
1. Output ONLY the full HTML file, starting with <!DOCTYPE html> and ending with </html>. No markdown fences, no explanation.
2. Use this exact CSS design system (DARK theme with blue accent). Every rule below must appear exactly:
   - `*{{margin:0;padding:0;box-sizing:border-box}}`
   - `body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:#e6e6e6;background:#0d1117}}`
   - `header{{background:#161b22;border-bottom:1px solid #30363d;padding:1rem 1.5rem}}`
   - `.container{{max-width:720px;margin:0 auto;padding:0 1.5rem}}`
   - `header .container{{display:flex;align-items:center;justify-content:space-between;max-width:960px}}`
   - `.logo{{font-size:1.4rem;font-weight:700;color:#58a6ff;text-decoration:none;font-family:"SF Mono",Monaco,monospace}}`
   - `nav a{{margin-left:1.5rem;color:#8b949e;text-decoration:none;font-size:.95rem}}`
   - `main{{padding:3rem 0}}`
   - `h1{{font-size:2rem;margin-bottom:1rem;color:#f0f6fc}}`
   - `h2{{font-size:1.3rem;margin:2rem 0 1rem;color:#f0f6fc}}`
   - `h3{{font-size:1.05rem;margin:1.5rem 0 .5rem;color:#f0f6fc}}`
   - `p{{margin-bottom:1rem;color:#c9d1d9}}`
   - `code{{background:#161b22;padding:.15rem .4rem;border-radius:4px;font-family:"SF Mono",Monaco,monospace;font-size:.9em;color:#7ee787}}`
   - `.tool-box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.5rem;margin:2rem 0}}`
   - `label{{display:block;font-weight:500;margin-bottom:.4rem;font-size:.9rem;color:#8b949e}}`
   - `textarea{{width:100%;padding:.75rem;background:#0d1117;border:1px solid #30363d;border-radius:6px;font-size:.95rem;color:#e6e6e6;font-family:"SF Mono",Monaco,monospace;min-height:120px;resize:vertical}}`
   - `textarea:focus{{outline:2px solid #58a6ff;border-color:transparent}}`
   - `input[type="text"],input[type="number"],input[type="email"],select{{width:100%;padding:.75rem;background:#0d1117;border:1px solid #30363d;border-radius:6px;font-size:.95rem;color:#e6e6e6;font-family:inherit}}`
   - `input:focus,select:focus{{outline:2px solid #58a6ff;border-color:transparent}}`
   - `.form-group{{margin-bottom:1.25rem}}`
   - `.output{{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:1rem;font-family:"SF Mono",Monaco,monospace;font-size:.85rem;color:#7ee787;word-break:break-all;min-height:2rem;margin-bottom:1rem;white-space:pre-wrap}}`
   - `.output-label{{font-size:.8rem;color:#6e7681;margin-bottom:.4rem;text-transform:uppercase;letter-spacing:.05em}}`
   - `button{{background:#238636;color:#fff;border:none;padding:.6rem 1.2rem;font-size:.95rem;font-weight:600;border-radius:6px;cursor:pointer}}`
   - `button:hover{{background:#2ea043}}`
   - `.secondary{{background:#21262d;border:1px solid #30363d}}`
   - `.secondary:hover{{background:#30363d}}`
   - `.button-row{{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.5rem}}`
   - `.lead-form{{margin-top:1.5rem;padding:1.25rem;background:#161b22;border:1px solid #30363d;border-radius:8px;display:none}}`
   - `.lead-form.show{{display:block}}`
   - `.lead-form button{{background:#238636;width:100%;margin-top:.5rem}}`
   - `.lead-form input[type="email"]{{width:100%;padding:.75rem;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#e6e6e6;font-size:1rem;margin-bottom:.5rem}}`
   - `.content-section{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.5rem;margin-bottom:2rem}}`
   - `footer{{border-top:1px solid #30363d;padding:2rem 0;margin-top:3rem;color:#6e7681;font-size:.9rem;background:#161b22}}`
   - `footer .container{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;max-width:960px}}`
   - `footer a{{color:#8b949e;text-decoration:none;margin-right:1rem}}`
   Do NOT use CSS custom properties. The primary action button MUST be #238636 green.
3. Header: `<header><div class="container"><a href="/" class="logo">devsecsuite</a><nav><a href="/about/">About</a><a href="/contact/">Contact</a></nav></div></header>`
4. Include a `<main><div class="container">` wrapper for all content.
5. Include a `.tool-box` with labeled inputs and a primary action button. Do NOT prefill any input field. No value="..." attribute on any input. No selected attribute on any option. All placeholder text should be a hint like "e.g., hello world" not a real value.
6. Include an `.output` area with `.output-label` above it showing "Result" or similar. The output updates live or when the button is clicked.
7. Include a `.lead-form` below the tool output that appears when output is generated. Use this exact form:
<form action="https://api.web3forms.com/submit" method="POST">
    <input type="hidden" name="access_key" value="d540b73c-53d0-46a3-8692-3827aedc2d77">
    <input type="email" name="email" required placeholder="your@email.com">
    <input type="hidden" name="tool" value="{item['name']}">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="subject" value="DevSecSuite subscriber — {item['name']}">
    <input type="hidden" name="redirect" value="https://devsecsuite.com/thank-you/">
    <button type="submit">Get Developer Tips Weekly</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>
No JavaScript alert functions.
8. Include a collapsible `<details>` section immediately below the calculator/tool (before content sections) titled "How this tool works". Inside: 2-3 sentences explaining the logic in plain English, plus one line: "Reference: [RFC or standard]." Use the correct standard for the tool (e.g., RFC 4122 for UUID, RFC 7519 for JWT, RFC 4648 for Base64). This <details> section is MANDATORY. Do not skip it.
9. Include 3 content sections, each wrapped in `<section class="content-section">`: "What Is [Tool Name]?", "Common Use Cases", and "Frequently Asked Questions" with 3 Q&As each. Each section 100-200 words with real developer-focused detail. Every content section MUST be wrapped in <section class="content-section">.
10. For FAQ, use `<h3>Question</h3><p>Answer</p>` for each Q&A. Never put multiple Q&As in one `<p>`. Never use "Q:" or "A:" prefixes.
11. Include footer: `<footer><div class="container"><div><a href="/">Home</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div><div>© 2026 DevSecSuite.</div></div></footer>`
12. Include JSON-LD schema: {{"@context":"https://schema.org","@type":"WebApplication","name":"{item['name']}","applicationCategory":"DeveloperApplication","operatingSystem":"Web","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}}}}
13. Include these two lines in the head exactly:
<script async src="https://www.googletagmanager.com/gtag/js?id=G-FVZSVQEB2C"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FVZSVQEB2C');</script>
14. Include AdSense in the head:
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2475849248056642" crossorigin="anonymous"></script>
15. Include in the head:
<link rel="canonical" href="https://devsecsuite.com/{item['slug']}/">
<title>{item['name']} — DevSecSuite</title>
<meta name="description" content="{item['description']}">
16. All JavaScript inline at bottom of body. Vanilla JS only. No external libraries unless absolutely required (and if required, embed minified).
17. Mobile responsive.
18. The tool must work correctly with the logic: {item['formula']}

Output the full HTML file now:"""


def call_provider(prompt, provider, model):
    """Single API call with a specific provider/model (OpenAI-compatible format)."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 32768,
    }
    req = urllib.request.Request(
        provider["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
            "User-Agent": UA,
            "HTTP-Referer": "https://devsecsuite.com",
            "X-Title": "DevSecSuite",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_PER_ATTEMPT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def call_with_retries(prompt, provider, model):
    """Try a provider+model combo with retries for transient errors."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"    Attempt {attempt + 1}/{MAX_RETRIES}")
            return call_provider(prompt, provider, model)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"    HTTP {e.code}: {body[:200]}")
            last_error = e
            if e.code in (401, 402, 403, 404):
                raise
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(10 * (attempt + 1))
                continue
            raise
        except (TimeoutError, urllib.error.URLError) as e:
            print(f"    Network error: {e}")
            last_error = e
            time.sleep(10 * (attempt + 1))
            continue
    raise RuntimeError(f"All retries failed: {last_error}")


def generate_with_fallback(prompt):
    """Try each provider+model in order until one succeeds."""
    errors = []
    for provider in PROVIDERS:
        for model in provider["models"]:
            print(f"Trying {provider['name']} / {model}")
            try:
                result = call_with_retries(prompt, provider, model)
                print(f"Success: {provider['name']} / {model}")
                return result
            except urllib.error.HTTPError as e:
                if e.code in (401, 402, 403):
                    print(f"  Auth/credit error — skipping remaining {provider['name']} models")
                    errors.append(f"{provider['name']}/{model}: {e.code}")
                    break
                errors.append(f"{provider['name']}/{model}: {e.code}")
                continue
            except Exception as e:
                errors.append(f"{provider['name']}/{model}: {e}")
                continue
    raise RuntimeError("All providers failed:\n" + "\n".join(errors))


def extract_html(text):
    text = text.strip()
    text = re.sub(r"^```html\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("<!DOCTYPE html>")
    if start == -1:
        start = text.find("<html")
    end = text.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")]
    if start != -1:
        print("WARNING: Truncated response, closing tags")
        truncated = text[start:]
        if "<body" in truncated:
            if "</body>" not in truncated:
                truncated += "\n</body>"
            if "</html>" not in truncated:
                truncated += "\n</html>"
            return truncated
    raise ValueError("Could not extract HTML")


def write_page(slug, html):
    os.makedirs(slug, exist_ok=True)
    path = os.path.join(slug, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {path} ({len(html)} bytes)")


def update_sitemap(slug):
    path = "sitemap.xml"
    with open(path, "r", encoding="utf-8") as f:
        sitemap = f.read()
    url = f"https://devsecsuite.com/{slug}/"
    if url in sitemap:
        return
    entry = f'<url><loc>{url}</loc><priority>0.9</priority></url>\n'
    sitemap = sitemap.replace("</urlset>", entry + "</urlset>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"Added {url} to sitemap")


def update_homepage(slug, name, description):
    path = "index.html"
    with open(path, "r", encoding="utf-8") as f:
        home = f.read()
    if f'href="/{slug}/"' in home:
        print("Already on homepage")
        return
    card = f'<a href="/{slug}/" class="card"><h3>{name}</h3><p>{description}</p></a>\n'
    last_grid = home.rfind('<div class="grid">')
    if last_grid == -1:
        print("Could not find grid")
        return
    close_idx = home.find("</div>", last_grid)
    if close_idx == -1:
        return
    home = home[:close_idx] + card + home[close_idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(home)
    print(f"Added {name} to homepage")


def main():
    queue = load_queue()
    idx, item = pick_next(queue)
    if item is None:
        print("Queue empty")
        return
    print(f"Generating: {item['name']} ({item['slug']})")
    prompt = build_prompt(item)
    raw = generate_with_fallback(prompt)
    html = extract_html(raw)
    write_page(item["slug"], html)
    update_sitemap(item["slug"])
    update_homepage(item["slug"], item["name"], item["description"])
    queue[idx]["status"] = "done"
    queue[idx]["generated_at"] = datetime.utcnow().isoformat() + "Z"
    save_queue(queue)
    print("Done.")


if __name__ == "__main__":
    main()
