PYTHON ?= python3
ENGINE ?= tectonic

.PHONY: check bundle

check:
	$(PYTHON) tests/check.py --engine "$(ENGINE)"

bundle:
	$(PYTHON) scripts/bundle.py
