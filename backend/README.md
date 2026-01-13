# Clockwork Hamlet Backend

FastAPI backend for the AI Village Simulation.

## Development

Requires [uv](https://docs.astral.sh/uv/) for package management.

```bash
# Install dependencies
uv sync

# Run server
uv run python -m hamlet.main

# Run tests
uv run pytest

# Lint code
uv run ruff check src tests

# Format code
uv run ruff format src tests

# Seed database
uv run python -m hamlet.db.seed

# Run simulation
uv run python -m hamlet.simulation.engine --ticks 10
```

Or use the Makefile from the project root:

```bash
make sync        # Install Python dependencies
make dev-backend # Run backend server
make test        # Run tests
make lint        # Lint all code
```
