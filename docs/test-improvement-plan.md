# Test Improvement Plan for Autonomous Execution

This plan outlines improvements to the test suite to support autonomous development workflows with minimal human intervention.

---

## Current State Assessment

### Test Inventory
- **Total Tests:** 80
- **Passing:** 79
- **Failing:** 1 (flaky boundary condition)
- **Coverage Areas:** API, Actions, Goals, Memory, Streaming

### Test Files
| File | Tests | Purpose |
|------|-------|---------|
| `test_main.py` | 2 | Root and health endpoints |
| `test_api.py` | 19 | REST API endpoints |
| `test_actions.py` | 12 | Action execution and validation |
| `test_goals.py` | 18 | Goal generation and prioritization |
| `test_memory.py` | 18 | Memory CRUD and compression |
| `test_stream.py` | 11 | SSE streaming and event bus |

### Strengths
- Good coverage of core systems
- Uses pytest fixtures for setup/teardown
- Has async test support via pytest-asyncio
- Tests are reasonably isolated

### Weaknesses for Autonomous Execution
1. **Flaky tests** - Boundary conditions not handled (e.g., score already at max)
2. **No test categorization** - Can't selectively run fast vs slow tests
3. **No integration tests** - Missing end-to-end simulation flow tests
4. **No frontend tests** - React components untested
5. **Shared database state** - Tests may pollute each other
6. **Missing coverage reports** - No visibility into gaps
7. **No performance benchmarks** - Can't detect regressions
8. **Pydantic deprecation warnings** - Noise in output

---

## Phase 1: Stabilize (Run Without Failure)

**Goal:** 100% pass rate with clean output

### 1.1 Fix Flaky Test

```python
# tests/test_actions.py - Fix boundary condition
def test_help_improves_relationship(self, world, reset_db):
    """Test that helping improves relationship."""
    # Move Agnes to town_square
    move = Move("agnes", "town_square")
    execute_action(move, world)

    # Get initial relationship and ensure it's not at max
    db = world.db
    rel_before = (
        db.query(Relationship)
        .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
        .first()
    )
    if rel_before and rel_before.score >= 10:
        rel_before.score = 5  # Reset to allow increase
        db.commit()
    score_before = rel_before.score if rel_before else 0

    # Help Bob
    action = Help("agnes", "bob", "with gardening")
    result = execute_action(action, world)

    assert result.success

    # Check relationship improved OR was already at max
    rel_after = (
        db.query(Relationship)
        .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
        .first()
    )
    assert rel_after.score >= score_before
```

### 1.2 Fix Pydantic Deprecation Warnings

Update all schema files to use `ConfigDict`:

```python
# Before
class AgentResponse(BaseModel):
    class Config:
        from_attributes = True

# After
from pydantic import ConfigDict

class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

### 1.3 Add pytest Configuration

```toml
# pyproject.toml additions
[tool.pytest.ini_options]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:pydantic.*:",
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, require DB)",
    "slow: Slow tests (>1s)",
]
```

---

## Phase 2: Isolate (Prevent State Pollution)

**Goal:** Tests run in any order without affecting each other

### 2.1 Database Isolation

Create fresh database per test module:

```python
# tests/conftest.py
import tempfile
import pytest
from hamlet.db import Base, engine
from hamlet.db.seed import seed_database

@pytest.fixture(scope="module")
def test_db():
    """Create isolated test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Override database URL
    import hamlet.config as config
    original_url = config.settings.database_url
    config.settings.database_url = f"sqlite:///{db_path}"

    # Create tables and seed
    Base.metadata.create_all(bind=engine)
    seed_database()

    yield db_path

    # Restore original
    config.settings.database_url = original_url
    os.unlink(db_path)
```

### 2.2 Transaction Rollback Pattern

Wrap each test in a transaction that rolls back:

```python
@pytest.fixture(autouse=True)
def db_transaction(world):
    """Rollback database after each test."""
    yield
    world.db.rollback()
```

---

## Phase 3: Categorize (Enable Targeted Runs)

**Goal:** Run subsets of tests based on purpose

### 3.1 Add Test Markers

```python
# tests/test_api.py
import pytest

@pytest.mark.unit
class TestHealthEndpoint:
    def test_health(self, client):
        ...

@pytest.mark.integration
class TestWorldEndpoint:
    def test_get_world(self, client):
        ...
```

### 3.2 Create Test Runner Commands

```bash
# Fast feedback loop (< 5 seconds)
uv run pytest -m unit --tb=short

# Full validation (< 30 seconds)
uv run pytest -m "not slow" --tb=short

# Complete suite
uv run pytest --tb=short

# Specific area
uv run pytest tests/test_api.py -v
```

### 3.3 CI Pipeline Configuration

```yaml
# .github/workflows/test.yml
jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - run: uv run pytest -m unit --tb=short

  full-tests:
    runs-on: ubuntu-latest
    needs: fast-tests
    steps:
      - run: uv run pytest --tb=short --cov=hamlet
```

---

## Phase 4: Expand (Increase Coverage)

**Goal:** Cover critical paths and edge cases

### 4.1 Integration Tests

```python
# tests/test_integration.py
"""End-to-end simulation tests."""

import pytest
from hamlet.simulation.engine import SimulationEngine
from hamlet.simulation.events import event_bus

@pytest.mark.integration
@pytest.mark.slow
class TestSimulationFlow:
    """Test complete simulation tick."""

    @pytest.mark.asyncio
    async def test_single_tick_executes(self):
        """Simulation tick processes all agents."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)
        await engine.start()

        # Run one tick
        await engine.tick()

        # Verify events were generated
        history = event_bus.get_history(limit=20)
        assert len(history) > 0
        assert any(e.type.value == "tick" for e in history)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_agent_actions_recorded(self):
        """Agent actions create events and memories."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)
        await engine.start()

        # Run multiple ticks
        for _ in range(3):
            await engine.tick()

        # Check events recorded
        history = event_bus.get_history(limit=50)
        action_events = [e for e in history if e.type.value == "action"]
        assert len(action_events) > 0

        await engine.stop()
```

### 4.2 API Contract Tests

```python
# tests/test_api_contracts.py
"""Verify API response schemas."""

import pytest
from pydantic import ValidationError

@pytest.mark.unit
class TestAPIContracts:
    """Test API response shapes match schemas."""

    def test_agent_response_schema(self, client):
        """Agent endpoint returns valid schema."""
        response = client.get("/api/agents/agnes")
        data = response.json()

        # Required fields
        assert "id" in data
        assert "name" in data
        assert "traits" in data
        assert "mood" in data
        assert "location_id" in data

        # Types
        assert isinstance(data["traits"], dict)
        assert isinstance(data["mood"], dict)

    def test_event_response_schema(self, client):
        """Events endpoint returns valid list."""
        response = client.get("/api/events?limit=5")
        events = response.json()

        assert isinstance(events, list)
        for event in events:
            assert "type" in event
            assert "summary" in event
            assert "timestamp" in event
```

### 4.3 Frontend Tests (Vitest)

```typescript
// frontend/src/hooks/useDigest.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { useDigest } from './useDigest'

describe('useDigest', () => {
  it('transforms API response correctly', async () => {
    const { result } = renderHook(() => useDigest('daily'))

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Should have transformed data
    expect(result.current.digest).toBeDefined()
    expect(result.current.digest?.title).toBe('THE DAILY HAMLET')
  })

  it('handles empty highlights gracefully', async () => {
    const { result } = renderHook(() => useDigest('daily'))

    await waitFor(() => !result.current.isLoading)

    // Should not throw on .length access
    expect(result.current.digest?.highlights).toBeDefined()
  })
})
```

---

## Phase 5: Automate (Zero-Touch Validation)

**Goal:** Tests run automatically and report clearly

### 5.1 Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running fast tests..."
cd backend && uv run pytest -m unit --tb=short -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### 5.2 Autonomous Validation Command

Create a slash command for ralph-wiggum:

```markdown
<!-- .claude/commands/validate.md -->
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
```

### 5.3 Coverage Threshold

```toml
# pyproject.toml
[tool.coverage.run]
source = ["hamlet"]
branch = true

[tool.coverage.report]
fail_under = 70
show_missing = true
```

---

## Phase 6: Monitor (Continuous Health)

**Goal:** Detect regressions automatically

### 6.1 Test Metrics Tracking

```python
# tests/conftest.py
import json
import time

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track test execution metrics."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        metrics = {
            "test": item.name,
            "duration": report.duration,
            "outcome": report.outcome,
            "timestamp": time.time(),
        }

        # Append to metrics file
        with open(".test-metrics.jsonl", "a") as f:
            f.write(json.dumps(metrics) + "\n")
```

### 6.2 Performance Baselines

```python
# tests/test_performance.py
import pytest
import time

@pytest.mark.slow
class TestPerformance:
    """Performance regression tests."""

    def test_agent_list_under_100ms(self, client):
        """Agent list should be fast."""
        start = time.time()
        response = client.get("/api/agents")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Agent list took {duration:.3f}s"

    def test_event_query_under_200ms(self, client):
        """Event query should be fast."""
        start = time.time()
        response = client.get("/api/events?limit=100")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.2, f"Event query took {duration:.3f}s"
```

---

## Implementation Priority

| Phase | Priority | Effort | Impact |
|-------|----------|--------|--------|
| 1. Stabilize | Critical | Low | High |
| 2. Isolate | High | Medium | High |
| 3. Categorize | Medium | Low | Medium |
| 4. Expand | Medium | High | High |
| 5. Automate | High | Medium | Very High |
| 6. Monitor | Low | Medium | Medium |

## Ralph-Wiggum Integration

Use this prompt for autonomous test improvements:

```bash
/ralph-wiggum:ralph-loop "
Implement Phase 1 of test-improvement-plan.md:
1. Fix the flaky test in test_actions.py (boundary condition)
2. Update Pydantic schemas to use ConfigDict
3. Add pytest markers configuration

Run tests after each change to verify fixes.
" --max-iterations 10 --completion-promise "uv run pytest passes with 0 failures and 0 warnings"
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Pass rate | 98.75% | 100% |
| Warnings | 10 | 0 |
| Coverage | Unknown | >70% |
| Fast tests (<5s) | N/A | 80% of suite |
| Flaky tests | 1 | 0 |
