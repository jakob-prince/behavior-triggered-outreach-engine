.PHONY: demo seed test lint typecheck check

# Run the end-to-end demo against synthetic leads.
demo:
	uv run python scripts/demo.py

# Regenerate the synthetic lead fixture (leads.json).
seed:
	uv run python scripts/seed_fake_data.py

test:
	uv run pytest -q

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

# Everything CI runs.
check: lint typecheck test