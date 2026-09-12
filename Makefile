PYTHON ?= python3
ENGINE ?= tectonic

.PHONY: check gallery bundle

check:
	$(PYTHON) tests/check.py --engine "$(ENGINE)"

gallery:
	$(PYTHON) scripts/gallery.py --engine "$(ENGINE)"

bundle:
	$(PYTHON) scripts/bundle.py
