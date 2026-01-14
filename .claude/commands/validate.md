# Validation Workflow

Run full validation suite and report results.

## Steps

1. Run backend tests:
   ```bash
   cd backend && uv run pytest --tb=short -q
   ```

2. Run backend linting:
   ```bash
   cd backend && uv run ruff check .
   ```

3. Run frontend build:
   ```bash
   cd frontend && npm run build
   ```

4. Run frontend lint:
   ```bash
   cd frontend && npm run lint
   ```

5. Report summary:
   - Tests: PASS/FAIL with count
   - Lint: PASS/FAIL with issue count
   - Build: PASS/FAIL

## Success Criteria
All steps pass with no errors.
