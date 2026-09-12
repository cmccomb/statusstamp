#!/usr/bin/env python3
"""Build an Overleaf-ready ZIP from an explicit list of distributable files."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
output = root / "build" / "statusstamp-overleaf.zip"
output.parent.mkdir(exist_ok=True)
files = {
    "statusstamp.sty": "statusstamp.sty",
    "examples/minimal.tex": "main.tex",
    "examples/configured.tex": "examples/configured.tex",
    "examples/gallery.tex": "examples/gallery.tex",
    "README.md": "README.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "LICENSE": "LICENSE",
}
if (root / "docs/gallery.png").exists():
    files["docs/gallery.png"] = "docs/gallery.png"
with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
    for source, destination in files.items():
        archive.write(root / source, destination)
print(output)
