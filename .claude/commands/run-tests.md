# Run Tests Command

Run the test suite with various options and report results.

## Arguments
- `$ARGUMENTS` - Optional: test path, markers, or flags
  - Empty: run all tests
  - `unit`: run only unit tests
  - `integration`: run only integration tests
  - `<path>`: run specific test file/directory
  - `--coverage`: include coverage report

## Workflow

1. **Navigate to backend:**
   ```bash
   cd /home/kai/code/repo/clockwork-hamlet/backend
   ```

2. **Construct pytest command based on arguments:**
   - Default: `uv run pytest tests/ -v --tb=short`
   - Unit only: `uv run pytest tests/ -v --tb=short -m unit`
   - Integration: `uv run pytest tests/ -v --tb=short -m integration`
   - Coverage: `uv run pytest tests/ -v --tb=short --cov=hamlet --cov-report=term-missing`
   - Specific path: `uv run pytest <path> -v --tb=short`

3. **Run tests and capture output**

4. **Parse results:**
   - Count passed/failed/skipped
   - Identify failing tests
   - Extract coverage percentage if applicable

5. **Report results:**
   ```markdown
   ## Test Results

   ### Summary
   - Passed: X
   - Failed: Y
   - Skipped: Z
   - Duration: N.Ns

   ### Failed Tests (if any)
   - `test_module::test_name`: <failure reason>

   ### Coverage (if requested)
   - Overall: X%
   - Uncovered: <files with low coverage>

   ### Verdict
   - PASS: All tests passing
   - FAIL: X tests need attention
   ```

## Success Criteria
- Tests executed successfully
- Clear report of results
- Actionable information for failures

## Notes
- Run before committing changes
- Use coverage flag periodically to check coverage
- Fix failing tests before marking work complete
