install:
    uv sync --all-extras --dev

ruff:
    uv run ruff format .
    uv run ruff check . --fix --unsafe-fixes

test:
    uv run pytest --cov=auto_token --codspeed --xdoc
    uv run coverage xml
