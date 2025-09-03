import os, re, shutil, yaml, pathlib

VAULT = pathlib.Path("/Users/hussam/Documents/Second Brain")  # <-- change me
DEST  = pathlib.Path("./docs")
DEST.mkdir(parents=True, exist_ok=True)

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

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
        out_name = f"{md.stem}.md"
        out_path = DEST / out_name
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
exported.sort(key=lambda t: t[0].lower())
lines = [
    '<div class="win98-window">',
    '  <div class="win98-titlebar"><span class="win98-icon"></span> Hussam — Notes</div>',
    '  <h3>Published notes</h3>',
    '  <ul class="win98-list">'
]
for title, fname in exported:
    if fname != "index.md":
        lines.append(f'    <li><a href="{fname}">{title}</a></li>')
lines += [
    '  </ul>',
    '</div>',
    ''
]
(DEST / "index.md").write_text("\n".join(lines), encoding="utf-8")

print(f"Exported {len(exported)} notes (index.md regenerated).")

