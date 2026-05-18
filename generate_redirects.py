"""
generate_redirects.py - Generate static HTML redirect pages from affiliate_redirects.yaml.

For each entry, writes public/go/<slug>/index.html that:
  1. Fires Vercel Web Analytics pageview (so you get click counts free)
  2. Meta-refresh + JS redirect to the destination
  3. Shows a 1-second "Redirecting to <dest>" splash so the user knows what's happening

Run after editing affiliate_redirects.yaml. Vercel auto-redeploys on push.
"""

import html
import json
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
YAML_PATH = BASE / "affiliate_redirects.yaml"
GO_DIR = BASE / "public" / "go"


REDIRECT_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Redirecting{title_suffix}</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="1;url={dest_attr}" />
<link rel="canonical" href="{dest_attr}" />
<style>
  body {{ background:#0a0a14; color:#e8e8ea; font-family:-apple-system,system-ui,sans-serif;
         display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; padding:2rem; }}
  .box {{ text-align:center; max-width:420px; }}
  h1 {{ font-size:1.1rem; margin:0 0 0.5rem; color:#c2a173; font-weight:500; }}
  p {{ font-size:0.92rem; margin:0; color:#aaa; line-height:1.5; }}
  a {{ color:#c2a173; }}
  .spinner {{ display:inline-block; width:14px; height:14px; border:2px solid #2a2a3a;
              border-top-color:#c2a173; border-radius:50%;
              animation:spin 0.9s linear infinite; margin-right:8px; vertical-align:middle; }}
  @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
</style>
</head>
<body>
<div class="box">
  <h1><span class="spinner"></span>{label}</h1>
  <p>Redirecting to <a href="{dest_attr}">{dest_display}</a>...</p>
</div>
<script>
  // Fire Vercel Analytics custom event so the click is tracked separately from pageview
  if (window.va) {{
    try {{ window.va('event', {{ name: 'affiliate_click', data: {{ slug: '{slug_js}', channel: '{channel_js}' }} }}); }}
    catch (e) {{}}
  }}
  // Hard redirect after 800ms (covers cases where meta-refresh is blocked)
  setTimeout(function() {{ window.location.href = {dest_json}; }}, 800);
</script>
<script defer src="/_vercel/insights/script.js"></script>
</body>
</html>
"""


def _truncate_dest(dest: str, n: int = 50) -> str:
    if len(dest) <= n:
        return dest
    return dest[: n - 1] + "..."


def generate() -> int:
    if not YAML_PATH.exists():
        print(f"ERROR: {YAML_PATH} not found", file=sys.stderr)
        return 1
    cfg = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    links = cfg.get("links", [])
    if not links:
        print("No links in YAML.")
        return 0

    GO_DIR.mkdir(parents=True, exist_ok=True)

    slugs_written = set()
    for entry in links:
        slug = entry.get("slug", "").strip()
        dest = entry.get("dest", "").strip()
        label = entry.get("label", slug)
        channel = entry.get("channel", "unknown")
        if not slug or not dest:
            print(f"WARN: skipping invalid entry: {entry}")
            continue

        if slug in slugs_written:
            print(f"WARN: duplicate slug '{slug}' — overwriting")
        slugs_written.add(slug)

        slug_dir = GO_DIR / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        out_path = slug_dir / "index.html"

        html_text = REDIRECT_HTML.format(
            title_suffix=f" - {html.escape(label)}",
            label=html.escape(label),
            dest_attr=html.escape(dest, quote=True),
            dest_display=html.escape(_truncate_dest(dest)),
            dest_json=json.dumps(dest),
            slug_js=html.escape(slug, quote=True),
            channel_js=html.escape(channel, quote=True),
        )
        out_path.write_text(html_text, encoding="utf-8")

    # Write a summary index at public/go/index.html so visitors landing on /go/ see what's there
    summary_rows = "\n".join(
        f'<tr><td><a href="/go/{html.escape(e["slug"])}/">/go/{html.escape(e["slug"])}/</a></td>'
        f'<td>{html.escape(e.get("label", ""))}</td>'
        f'<td>{html.escape(e.get("channel", ""))}</td></tr>'
        for e in links
        if e.get("slug")
    )
    summary_html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Affiliate redirects</title>
<meta name="robots" content="noindex">
<style>
body {{ font-family:-apple-system,system-ui,sans-serif; background:#0a0a14; color:#e8e8ea; max-width:900px; margin:2rem auto; padding:1rem; }}
table {{ width:100%; border-collapse:collapse; font-size:0.88rem; }}
th, td {{ padding:6px 12px; text-align:left; border-bottom:1px solid #2a2a3a; }}
th {{ color:#888; font-weight:500; text-transform:uppercase; font-size:0.74rem; letter-spacing:0.6px; }}
a {{ color:#c2a173; }}
</style></head><body>
<h1 style="color:#c2a173; margin-bottom:0.2rem;">Affiliate redirects ({len(links)})</h1>
<p style="color:#888; margin-top:0; font-size:0.85rem;">Static redirect targets. Each click counted by Vercel Analytics.</p>
<table><thead><tr><th>Path</th><th>Label</th><th>Channel</th></tr></thead>
<tbody>{summary_rows}</tbody></table></body></html>"""
    (GO_DIR / "index.html").write_text(summary_html, encoding="utf-8")

    print(f"Generated {len(slugs_written)} redirect page(s) in public/go/")
    return 0


if __name__ == "__main__":
    sys.exit(generate())
