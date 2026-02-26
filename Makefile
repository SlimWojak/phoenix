.PHONY: truth-sync test lint check-isolation

truth-sync:
	python scripts/validate_registry.py
	python scripts/validate_manifest.py

test:
	python -m pytest -o addopts='' -q --tb=short

lint:
	python -m ruff check .

check-isolation:
	python scripts/check_economy_isolation.py
