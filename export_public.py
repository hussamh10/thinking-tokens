import os, re, shutil, yaml, pathlib

VAULT = pathlib.Path("/Users/hussam/Documents/Second Brain")  # <-- change me
DEST  = pathlib.Path("./docs")
DEST.mkdir(parents=True, exist_ok=True)

def wants_publish(p: pathlib.Path) -> bool:
    try:
        text = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not m: return False
        fm = yaml.safe_load(m.group(1)) or {}
        return fm.get("publish", False) is True
    except Exception:
        return False

def fix_wikilinks(s: str) -> str:
    # [[Note]] or [[Note|Alias]] -> Note.md
    return re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", r"\1.md", s)

# clear docs/ except index.md if you hand-wrote it
for p in DEST.glob("*.md"):
    if p.name != "index.md":
        p.unlink()

for md in VAULT.rglob("*.md"):
    if wants_publish(md):
        out = DEST / md.name
        txt = md.read_text(encoding="utf-8")
        out.write_text(fix_wikilinks(txt), encoding="utf-8")

assets_src = VAULT / "Public" / "assets"
assets_dst = DEST / "assets"
if assets_src.exists():
    if assets_dst.exists(): shutil.rmtree(assets_dst)
    shutil.copytree(assets_src, assets_dst)
print("Exported selected notes.")

