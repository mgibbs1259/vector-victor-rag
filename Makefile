.PHONY: fix

fix:
	python -m black .
	ruff check . --fix