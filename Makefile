PYTHON ?= python3
ENGINE ?= tectonic

.PHONY: check gallery bundle ctan

check:
	$(PYTHON) tests/check.py --engine "$(ENGINE)"

gallery:
	$(PYTHON) scripts/gallery.py --engine "$(ENGINE)"

bundle:
	$(PYTHON) scripts/bundle.py

ctan:
	tectonic --outdir docs docs/statusstamp-manual.tex
	tectonic -Z search-path=. --outdir examples examples/statusstamp-example-minimal.tex
	tectonic -Z search-path=. --outdir examples examples/statusstamp-example-configured.tex
	$(PYTHON) scripts/ctan.py
