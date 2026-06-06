.PHONY: help install lint typecheck test eval plots clean

DATA ?= tests/fixtures/billsum_mini.jsonl

help:
	@echo "make install                       - deps"
	@echo "make lint / typecheck / test       - quality gates"
	@echo "make eval DATA=path                - score the JSONL"
	@echo "make plots                         - regenerate the chart set"

install: ; uv sync --all-extras
lint:
	uv run ruff check src tests
	uv run ruff format --check src tests
typecheck: ; uv run mypy src
test: ; uv run pytest -m "not slow and not needs_provider"
eval: ; uv run lse score --data $(DATA)
plots: ; uv run lse plots --out-dir results/figures
clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
