import os, re, shutil, yaml, pathlib

VAULT = pathlib.Path("/Users/hussam/Documents/Second Brain")  # <-- change me
DEST  = pathlib.Path("./docs")
DEST.mkdir(parents=True, exist_ok=True)

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def slugify(name: str) -> str:
    # Drop extension, lowercase, replace spaces with dashes, strip bad chars
    base = re.sub(r"\.md$", "", name, flags=re.IGNORECASE)
    base = base.strip().lower()
    base = re.sub(r"[ _]+", "-", base)          # spaces/underscores -> -
    base = re.sub(r"[^a-z0-9\-]+", "", base)    # keep alnum + dashes
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base or "index"

USE_DIRECTORY_URLS = True   # set False if you use use_directory_urls: false

def parse_front_matter(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return fm, body

def wants_publish(p: pathlib.Path) -> bool:
    try:
        text = p.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(text)
        return bool(fm.get("publish", False))
    except Exception:
        return False

def fix_wikilinks(s: str) -> str:
    # [[Note]] / [[Note|Alias]] / [[Note#Heading]] -> Note.md
    return re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", r"\1.md", s)

exported = []

# Clear docs/ except assets/
for p in DEST.glob("*.md"):
    p.unlink()

for md in VAULT.rglob("*.md"):
    if not md.is_file():
        continue
    if wants_publish(md):
        txt = md.read_text(encoding="utf-8")
        fm, body = parse_front_matter(txt)
        title = fm.get("title") or md.stem
        safe_name = slugify(md.stem) + ".md"
        out_path = DEST / safe_name
        out_path.write_text(fix_wikilinks(txt), encoding="utf-8")
        if out_name != "index.md":
            exported.append((title, out_name))

# Copy assets if you use them
assets_src = VAULT / "Public" / "assets"
assets_dst = DEST / "assets"
if assets_src.exists():
    if assets_dst.exists(): shutil.rmtree(assets_dst)
    shutil.copytree(assets_src, assets_dst)

# Always regenerate index.md

# Always regenerate index.md
exported.sort(key=lambda t: t[0].lower())

def mkdocs_href(out_name: str) -> str:
    slug = slugify(out_name)
    return f"{slug}/" if USE_DIRECTORY_URLS else f"{slug}.html"

lines = [
    '<div class="win98-window">',
    '  <div class="win98-titlebar"><span class="win98-icon"></span> Hussam — Thinking Tokens</div>',
    '  <ul class="win98-list">'
]
for title, fname in exported:
    if fname != "index.md":
        href = mkdocs_href(fname)
        lines.append(f'    <li><a href="{href}">{title}</a></li>')
lines += [
    '  </ul>',
    '</div>',
    ''
]

# ✅ write the homepage
(DEST / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Exported {len(exported)} notes (index.md regenerated).")

