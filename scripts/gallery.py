#!/usr/bin/env python3
"""Compile the real example pages and regenerate the README contact sheet."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "gallery"
DOCS = ROOT / "docs"


def compile_example(engine, name, expected_pages):
    env = dict(os.environ, TEXINPUTS=f"{ROOT}{os.pathsep}" + os.environ.get("TEXINPUTS", ""))
    env["PATH"] = f"{Path(engine).parent}{os.pathsep}" + env.get("PATH", "")
    source = ROOT / "examples" / f"{name}.tex"
    if Path(engine).name == "tectonic":
        command = [engine, "-Z", f"search-path={ROOT}", "--keep-logs", "--outdir", str(BUILD), str(source)]
        passes = 1
    else:
        command = [engine, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape",
                   f"-output-directory={BUILD}", str(source)]
        passes = 2
    for _ in range(passes):
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
        if result.returncode:
            raise RuntimeError(f"{name}: compilation failed\n{result.stdout}\n{result.stderr}")
    log = (BUILD / f"{name}.log").read_text(errors="replace")
    for problem in ["Overfull", "Missing character:", "LaTeX Font Warning:"]:
        if problem in log:
            raise RuntimeError(f"{name}: {problem}; inspect {BUILD / (name + '.log')}")
    path = BUILD / f"{name}.pdf"
    with fitz.open(path) as pdf:
        if len(pdf) != expected_pages:
            raise RuntimeError(f"{name}: expected {expected_pages} pages, got {len(pdf)}")
        fitz.TOOLS.mupdf_warnings(reset=True)
        for page in pdf:
            page.get_pixmap()
        warnings = fitz.TOOLS.mupdf_warnings(reset=True)
        if warnings:
            raise RuntimeError(f"{name}: PDF rendering warnings: {warnings}")
    shutil.copy2(path, DOCS / path.name)
    print(f"Built {name}.pdf ({expected_pages} pages)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="tectonic", help="TeX engine name or path")
    args = parser.parse_args()
    engine = shutil.which(args.engine)
    if not engine:
        raise SystemExit(f"TeX engine not found: {args.engine}")
    BUILD.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    compile_example(engine, "gallery-samples", 14)
    compile_example(engine, "gallery", 1)
    with fitz.open(DOCS / "gallery.pdf") as pdf:
        pdf[0].get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False).save(DOCS / "gallery.png")
    print(f"Updated {DOCS / 'gallery.png'}", flush=True)


if __name__ == "__main__":
    main()
