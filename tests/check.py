#!/usr/bin/env python3
"""Compile real documents and inspect their rendered pages and text positions."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

import pymupdf as fitz

fitz.TOOLS.mupdf_display_errors(False)

ROOT = Path(__file__).resolve().parents[1]
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--engine", default="tectonic", help="TeX engine name or path")
ARGS = PARSER.parse_args()
ENGINE = shutil.which(ARGS.engine)
if not ENGINE:
    raise SystemExit(f"TeX engine not found: {ARGS.engine}")
BUILD = ROOT / "build" / Path(ENGINE).name
BUILD.mkdir(parents=True, exist_ok=True)


def compile_tex(name, source, fail=False):
    tex = BUILD / f"{name}.tex"
    tex.write_text(source)
    env = dict(os.environ, TEXINPUTS=f"{ROOT}{os.pathsep}" + os.environ.get("TEXINPUTS", ""))
    env["PATH"] = f"{Path(ENGINE).parent}{os.pathsep}" + env.get("PATH", "")
    if Path(ENGINE).name == "tectonic":
        cmd = [ENGINE, "-Z", f"search-path={ROOT}", "--keep-logs", "--outdir", str(BUILD), str(tex)]
        passes = 1  # Tectonic handles reruns itself.
    else:
        cmd = [ENGINE, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape",
               f"-output-directory={BUILD}", str(tex)]
        passes = 2
    for _ in range(passes):
        result = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
        if fail:
            assert result.returncode != 0, f"{name}: invalid input was accepted"
            return result.stdout + result.stderr
        if result.returncode:
            raise AssertionError(f"{name}: compilation failed\n{result.stdout}\n{result.stderr}")
    log = tex.with_suffix(".log").read_text(errors="replace")
    assert "Missing character:" not in log, f"{name}: missing glyph"
    if "LaTeX Font Warning:" in log:
        warning = log[log.index("LaTeX Font Warning:"):][:500]
        raise AssertionError(f"{name}: unexpected font warning\n{warning}")
    pdf = fitz.open(tex.with_suffix(".pdf"))
    # A successful TeX exit is insufficient: catch malformed PDF resources.
    fitz.TOOLS.mupdf_warnings(reset=True)
    for page in pdf:
        page.get_pixmap()
    warnings = fitz.TOOLS.mupdf_warnings(reset=True)
    assert not warnings, f"{name}: PDF rendering errors: {warnings[:600]}"
    return pdf


def document(preamble="", body=None, options="letterpaper", cls="article"):
    if body is None:
        # Reset the printed page number twice: selection must use physical pages.
        body = r"""
\section*{Layout check}
\noindent LayoutToken: The stamp must not move this paragraph or change its font.
\par\medskip\noindent\textsf{SansToken: The document keeps its original sans serif family.}
\newpage\setcounter{page}{1}
\noindent LayoutToken: This is the second physical page.
\newpage\setcounter{page}{1}
\noindent LayoutToken: This is the third physical page.
"""
    return (rf"\documentclass[11pt]{{{cls}}}" + "\n" +
            r"\usepackage[T1]{fontenc}" + "\n" +
            rf"\usepackage[{options},margin=1in]{{geometry}}" + "\n" +
            preamble + "\n" + r"\begin{document}" + "\n" + body + "\n" + r"\end{document}" + "\n")


def raster(page):
    return page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), colorspace=fitz.csRGB, alpha=False)


def mark_pages(pdf, text="SUBMITTED"):
    return [i + 1 for i, page in enumerate(pdf) if text in page.get_text()]


def spans(pdf):
    result = []
    for page in pdf:
        # Bitmap Type3 font names (F44, F45, ...) are PDF resource IDs, not
        # font identities. Allocation changes when the stamp font is loaded.
        # The separate full-page raster equality check verifies these glyphs.
        bitmap_ids = {font[3] for font in page.get_fonts() if font[2] == "Type3"}
        result.append([(span["text"], "Type3" if span["font"] in bitmap_ids else span["font"],
                        tuple(round(v, 3) for v in span["bbox"]))
                       for block in page.get_text("dict")["blocks"] if "lines" in block
                       for line in block["lines"] for span in line["spans"]
                       if "SUBMITTED" not in span["text"]])
    return result


def check():
    baseline = compile_tex("baseline", document())
    disabled = compile_tex("disabled", document(r"\usepackage[enabled=false]{statusstamp}"))
    assert len(baseline) == len(disabled) == 3
    assert spans(baseline) == spans(disabled), ("Loading the disabled package changed text layout or fonts\n"
                                               f"Baseline: {spans(baseline)}\nDisabled: {spans(disabled)}")
    assert all(raster(a).samples == raster(b).samples for a, b in zip(baseline, disabled))

    for selection, expected in [("all", [1, 2, 3]), ("first", [1]), ("odd", [1, 3]), ("even", [2])]:
        pdf = compile_tex(selection, document(rf"\usepackage[pages={selection}]{{statusstamp}}"))
        assert len(pdf) == 3 and mark_pages(pdf) == expected, f"Incorrect physical page selection: {selection}"
        assert spans(pdf) == spans(baseline), (f"The {selection} stamp changed layout or fonts\n"
                                             f"Baseline: {spans(baseline)}\nStamped: {spans(pdf)}")

    blank_body = r"\pagestyle{empty}\null"
    # Freeze the original drawing, but prebuild it outside shipout so XeTeX
    # declares its opacity resources before the first page (the original
    # proposal's lazy activation is not portable to that backend).
    reference = (r"\input{tests/fixtures/original-stamp.tex}\newsavebox{\referencebox}"
                 r"\AtBeginDocument{\sbox{\referencebox}{\FinalStamp}}"
                 r"\AddToShipoutPictureBG{\AtPageCenter{\makebox(0,0){\usebox{\referencebox}}}}")
    original = compile_tex("original", document(reference, blank_body))
    extracted = compile_tex("extracted", document(r"\usepackage{statusstamp}", blank_body))
    a, b = raster(original[0]), raster(extracted[0])
    assert (a.width, a.height) == (b.width, b.height)
    mean_error = sum(abs(x - y) for x, y in zip(a.samples, b.samples)) / len(a.samples)
    assert mean_error < .2, f"Original stamp appearance changed (mean channel error {mean_error:.4f})"
    print(f"Original appearance: mean raster channel error {mean_error:.6f}/255", flush=True)

    # Same fixed wear pattern on repeated pages; no automatic date or changing seed.
    repeated = compile_tex("repeated", document(r"\usepackage{statusstamp}",
                           r"\pagestyle{empty}\null\newpage\null"))
    assert raster(repeated[0]).samples == raster(repeated[1]).samples

    compile_tex("no-fontenc", document(r"\usepackage{statusstamp}", blank_body).replace(
        r"\usepackage[T1]{fontenc}", ""))

    transparent = compile_tex("transparent", document(r"\usepackage[opacity=0]{statusstamp}", blank_body))
    assert min(raster(transparent[0]).samples) == 255

    for position in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        pdf = compile_tex(position, document(
            rf"\usepackage[position={position},scale=.45,margin=1cm,distressed=false]{{statusstamp}}",
            blank_body, options="a4paper,landscape"))
        rect = pdf[0].search_for("SUBMITTED")[0]
        page = pdf[0].rect
        assert page.contains(rect), f"Clipped label at {position}"
        assert (rect.x0 > page.width / 2) == ("right" in position)
        assert (rect.y0 > page.height / 2) == ("bottom" in position)

    custom = compile_tex("custom", document(
        r"\usepackage{statusstamp}\statusstampsetup{text=ACCEPTED,date={12 September 2026},"
        r"color=blue,angle=-8,opacity=.5,scale=.65,seed=42,distressed=false,layer=foreground}", blank_body,
        cls="report"))
    assert "ACCEPTED" in custom[0].get_text() and "12 September 2026" in custom[0].get_text()

    # An opaque page background must hide a background stamp, but not a foreground stamp.
    cover = r"\usepackage{tikz}\AddToHook{shipout/background}[cover]{\put(0,0){"
    cover += r"\begin{tikzpicture}[overlay]\fill[white] (0,0) rectangle (\paperwidth,-\paperheight);\end{tikzpicture}}}"
    covered_bg = compile_tex("covered-bg", document(r"\usepackage{statusstamp}" + cover +
        r"\DeclareHookRule{shipout/background}{statusstamp}{before}{cover}", blank_body))
    covered_fg = compile_tex("covered-fg", document(r"\usepackage[layer=foreground]{statusstamp}" + cover, blank_body))
    assert min(raster(covered_bg[0]).samples) == 255, "Background layering is wrong"
    assert min(raster(covered_fg[0]).samples) < 200, "Foreground layering is wrong"

    rng = r"""
\makeatletter
\pgfmathsetseed{12345}\pgfmathparse{rnd}\let\expected\pgfmathresult
\pgfmathsetseed{12345}\sbox0{\statusstamp[scale=.25]}
\pgfmathparse{rnd}
\ifx\expected\pgfmathresult\else\errmessage{Stamp changed the PGF random sequence}\fi
\makeatother
\null
"""
    compile_tex("random-state", document(r"\usepackage[enabled=false]{statusstamp}", rng))
    toggle = compile_tex("toggle", document(r"\usepackage{statusstamp}",
        r"\null\clearpage\statusstampsetup{enabled=false}\null\clearpage"
        r"\statusstampsetup{enabled=true,text=ACCEPTED}\null"))
    assert mark_pages(toggle) == [1] and mark_pages(toggle, "ACCEPTED") == [3]

    for value, message in [("scale=0", "Scale must be positive"),
                           ("opacity=2", "Opacity must be between"),
                           ("pages=unknown", "unknown")]:
        output = compile_tex("invalid-" + value.split("=")[0],
                             document(rf"\usepackage[{value}]{{statusstamp}}"), fail=True)
        assert message in output

    for example in ["minimal", "configured", "gallery"]:
        compile_tex(example, (ROOT / "examples" / f"{example}.tex").read_text())
    print(f"PASS: {Path(ENGINE).name}: appearance, layout, fonts, pages, placement, layers, "
          "random state, toggles, input validation, and examples", flush=True)


if __name__ == "__main__":
    check()
