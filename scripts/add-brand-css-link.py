"""Add /_brand/brand.css <link> to every tool index.html that's missing it.

Idempotent — safe to re-run.

Skips:
- /_brand/ (the brand itself)
- /go/ (affiliate redirect pages — not visual tools)
- /icons/ (icon assets)
- The top-level /index.html (already styled inline)
"""
import re
from pathlib import Path


PUBLIC = Path(__file__).parent.parent / "public"
LINK_TAG = '<link rel="stylesheet" href="/_brand/brand.css">'
LINK_MARKER = "/_brand/brand.css"


def should_skip(p: Path) -> bool:
    parts = p.parts
    if "_brand" in parts or "go" in parts or "icons" in parts:
        return True
    # Skip the top-level public/index.html (homepage has its own styling)
    if p.parent == PUBLIC:
        return True
    return False


def add_link_to_file(path: Path) -> str:
    """Returns 'added', 'present', or 'noviewport'."""
    text = path.read_text(encoding="utf-8")
    if LINK_MARKER in text:
        return "present"

    # Insert AFTER viewport meta (most consistent landmark)
    viewport_re = re.compile(
        r'(<meta\s+name="viewport"[^>]*>)',
        re.IGNORECASE,
    )
    m = viewport_re.search(text)
    if m:
        idx = m.end()
        new_text = text[:idx] + "\n" + LINK_TAG + text[idx:]
        path.write_text(new_text, encoding="utf-8")
        return "added"

    # Fallback: insert before </head>
    head_re = re.compile(r"</head>", re.IGNORECASE)
    m = head_re.search(text)
    if m:
        idx = m.start()
        new_text = text[:idx] + LINK_TAG + "\n" + text[idx:]
        path.write_text(new_text, encoding="utf-8")
        return "added"

    return "noviewport"


added = 0
present = 0
skipped = 0
failed = 0

for index_html in PUBLIC.rglob("index.html"):
    if should_skip(index_html):
        skipped += 1
        continue
    result = add_link_to_file(index_html)
    rel = index_html.relative_to(PUBLIC)
    if result == "added":
        added += 1
        print(f"  ADD  {rel}")
    elif result == "present":
        present += 1
    else:
        failed += 1
        print(f"  FAIL {rel}")

print(f"\nadded={added} present={present} skipped={skipped} failed={failed}")
