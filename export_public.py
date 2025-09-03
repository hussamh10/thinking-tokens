#!/usr/bin/env python3
import os, sys, re, shutil, pathlib, yaml
from collections import defaultdict

# ------------------ CONFIG ------------------ #
VAULT = pathlib.Path("/Users/hussam/Documents/Second Brain")  # <— change to your vault
DEST  = pathlib.Path("./docs")
ASSETS_SRC = VAULT / "Public" / "assets"     # optional
ASSETS_DST = DEST / "assets"
HOMEPAGE_TITLE = "Hussam — Thinking Tokens"
USE_DIRECTORY_URLS = True                    # must match mkdocs.yml
MISC_LABEL = "Misc"                          # bucket for root-level files

# ------------------ GUARDS ------------------ #
DEST.mkdir(parents=True, exist_ok=True)
if os.getenv("GITHUB_ACTIONS") == "true" or not VAULT.exists():
    print("Exporter skipped (CI environment or vault path missing).")
    sys.exit(0)

# ------------------ HELPERS ------------------ #
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def parse_front_matter(text: str):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return fm, body

def slugify_name(name: str) -> str:
    base = re.sub(r"\.md$", "", name, flags=re.IGNORECASE).strip().lower()
    base = re.sub(r"[ _]+", "-", base)
    base = re.sub(r"[^a-z0-9\-]+", "", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base or "index"

def mkdocs_href_from_slug(slug: str) -> str:
    return f"{slug}/" if USE_DIRECTORY_URLS else f"{slug}.html"

def wants_publish(md_path: pathlib.Path) -> bool:
    try:
        text = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(text)
        return bool(fm.get("publish", False))
    except Exception:
        return False

def fix_wikilinks_to_slugs(text: str) -> str:
    def repl(m):
        target = m.group(1)  # before | or #
        return f"{slugify_name(target)}.md"
    return re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", repl, text)

def infer_section_parts(md_path: pathlib.Path, fm: dict) -> list[str]:
    """
    Returns a list of section parts like ["Research","Quran","Tafsir"].
    Priority:
      1) front-matter: section: "A/B/C"  (slashes create levels)
      2) first N folders under VAULT (auto, unlimited depth)
      3) [MISC_LABEL]
    """
    # 1) explicit
    if isinstance(fm.get("section", None), str) and fm["section"].strip():
        parts = [p.strip() for p in fm["section"].split("/") if p.strip()]
        return parts if parts else [MISC_LABEL]
    # 2) folders under vault
    try:
        rel = md_path.relative_to(VAULT)
        folder_parts = list(rel.parts[:-1])  # exclude filename
        if folder_parts:
            return folder_parts
    except Exception:
        pass
    # 3) fallback
    return [MISC_LABEL]

# Simple tree node structure
def tree():
    return {"children": {}, "items": []}
root = tree()

def insert_into_tree(parts: list[str], item_tuple: tuple[str,str]):
    """
    parts: section path parts, e.g. ["Research","Quran"]
    item_tuple: (title, slug)
    """
    node = root
    for p in parts:
        if p not in node["children"]:
            node["children"][p] = tree()
        node = node["children"][p]
    node["items"].append(item_tuple)

def render_tree(node, depth=0) -> list[str]:
    """
    Recursively render the tree into nested HTML.
    Uses <h3>, <h4>, <h5>, … for headings by depth,
    and <ul class="win98-list"> for item lists.
    """
    html = []
    # Render children sections in alpha order
    for sec_name in sorted(node["children"].keys(), key=lambda s: s.lower()):
        h_level = min(3 + depth, 6)  # cap at h6
        html.append(f'  <h{h_level}>{sec_name}</h{h_level}>')
        html.extend(render_tree(node["children"][sec_name], depth+1))
    # Render items (notes) in alpha order
    if node["items"]:
        html.append('  <ul class="win98-list">')
        for title, slug in sorted(node["items"], key=lambda t: t[0].lower()):
            href = mkdocs_href_from_slug(slug)
            html.append(f'    <li><a href="{href}">{title}</a></li>')
        html.append('  </ul>')
    return html

def homepage_shell(inner_html: str) -> str:
    return "\n".join([
        # Front matter: hide page title + nav/toc/footer on this page
        '---',
        'title: ""',
        'hide:',
        '  - navigation',
        '  - toc',
        '  - footer',
        '  - title',
        '---',
        # Add a class to body so we can style the homepage specially
        '<script>document.body.classList.add("home-index");</script>',
        '',
        '<div class="win98-window">',
        f'  <div class="win98-titlebar"><span class="win98-icon"></span> {HOMEPAGE_TITLE}</div>',
        inner_html,
        '</div>',
        ''
    ])


# ------------------ CLEAN DEST ------------------ #
for p in DEST.glob("*.md"):
    p.unlink()

# ------------------ EXPORT ------------------ #
for md in VAULT.rglob("*.md"):
    if not md.is_file():
        continue
    if not wants_publish(md):
        continue

    raw = md.read_text(encoding="utf-8")
    fm, _ = parse_front_matter(raw)
    title = (fm.get("title") or md.stem).strip()
    slug  = slugify_name(md.stem)
    out_path = DEST / f"{slug}.md"

    cooked = fix_wikilinks_to_slugs(raw)
    out_path.write_text(cooked, encoding="utf-8")

    if slug != "index":
        insert_into_tree(infer_section_parts(md, fm), (title, slug))

# Copy assets (optional)
if ASSETS_SRC.exists():
    if ASSETS_DST.exists():
        shutil.rmtree(ASSETS_DST)
    shutil.copytree(ASSETS_SRC, ASSETS_DST)

# ------------------ HOMEPAGE (multi-level) ------------------ #
content_lines = render_tree(root, depth=0)
index_md = homepage_shell("\n".join(content_lines))
(DEST / "index.md").write_text(index_md, encoding="utf-8")

# Stats
def count_nodes(n):
    c = len(n["items"])
    for ch in n["children"].values():
        c += count_nodes(ch)
    return c
print(f"Exported {count_nodes(root)} notes into multi-level sections -> {DEST}")

