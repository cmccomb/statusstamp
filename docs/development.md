# Development

[Back to the README](../README.md)

Run these commands from the repository root. The checks and gallery build need
Python 3.10+, PyMuPDF, and a TeX engine with the package
[dependencies](usage.md#requirements).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
make check PYTHON=.venv/bin/python ENGINE=tectonic
make gallery PYTHON=.venv/bin/python ENGINE=tectonic
make bundle PYTHON=.venv/bin/python
```

`ENGINE` can also be `pdflatex`, `xelatex`, or `lualatex`, or an absolute path
to one of those engines. GitHub Actions checks all three TeX Live engines.
The suite compares the default drawing with a frozen extraction of the
original stamp; checks rendering, fonts, text positions, page selection,
corner placement, layering, random state, toggles, and invalid settings; and
compiles each example. Build output stays under `build/`.

`make gallery` compiles the fourteen miniature pages in
[`examples/gallery-samples.tex`](../examples/gallery-samples.tex), assembles them
with [`examples/gallery.tex`](../examples/gallery.tex), and regenerates the PDFs
and README image in `docs/`. The sheet shows each sample's settings. Its small
pages use a 0.35 cm corner inset; normal documents default to 1 cm. Building
the sheet also requires the Latin Modern fonts (`lmodern`).

To compile only an example from the repository root:

```sh
mkdir -p build
tectonic -Z search-path=. --outdir build examples/minimal.tex
# Or with TeX Live:
pdflatex -output-directory=build examples/minimal.tex
```

`make bundle` creates `build/statusstamp-overleaf.zip` containing the package,
a root `main.tex` example, the other examples, README, changelog, and license.
It does not publish or upload anything.

