#!/usr/bin/env python3
"""Build the CTAN upload archive from an explicit file list."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
manual_source = root / "docs/statusstamp-manual.tex"
manual_pdf = root / "docs/statusstamp-manual.pdf"
if not manual_pdf.exists() or manual_pdf.stat().st_mtime < manual_source.stat().st_mtime:
    raise SystemExit("Compile docs/statusstamp-manual.tex before building the CTAN archive.")

files = {
    "packaging/ctan-README.md": "README.md",
    "statusstamp.sty": "statusstamp.sty",
    "docs/statusstamp-manual.tex": "statusstamp-manual.tex",
    "docs/statusstamp-manual.pdf": "statusstamp-manual.pdf",
    "examples/statusstamp-example-minimal.tex": "statusstamp-example-minimal.tex",
    "examples/statusstamp-example-minimal.pdf": "statusstamp-example-minimal.pdf",
    "examples/statusstamp-example-configured.tex": "statusstamp-example-configured.tex",
    "examples/statusstamp-example-configured.pdf": "statusstamp-example-configured.pdf",
    "CHANGELOG.md": "CHANGELOG.md",
    "LICENSE": "LICENSE",
}
output = root / "build/statusstamp-ctan-0.1.0.zip"
output.parent.mkdir(exist_ok=True)
with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
    for source, destination in files.items():
        path = root / source
        if not path.is_file():
            raise SystemExit(f"Missing archive file: {path}")
        archive.write(path, f"statusstamp/{destination}")
print(output)
