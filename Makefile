.PHONY: fix

fix:
	python -m black .
	ruff check --select I --fix
	ruff format