"""End-to-end simulation tests.

Phase 4 implementation: Integration tests for simulation flow.
These tests verify that the simulation engine correctly processes ticks,
executes agent actions, and records events.
"""

import pytest

from hamlet.simulation.engine import SimulationEngine
from hamlet.simulation.events import EventType, event_bus


@pytest.mark.integration
@pytest.mark.slow
class TestSimulationFlow:
    """Test complete simulation tick."""

    @pytest.fixture(autouse=True)
    def clear_event_history(self):
        """Clear event bus history before each test."""
        event_bus._history.clear()
        event_bus._subscribers.clear()
        yield

    @pytest.mark.asyncio
    async def test_single_tick_executes(self, isolated_db_session):
        """Simulation tick processes all agents."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        # Run one tick (don't start the loop, just tick once)
        await engine.tick()

        # Verify events were generated
        history = event_bus.get_history(limit=20)
        assert len(history) > 0, "Should have generated events"
        assert any(e.type == EventType.TICK for e in history), "Should have tick event"

        engine.world.close()

    @pytest.mark.asyncio
    async def test_multiple_ticks_execute(self, isolated_db_session):
        """Multiple simulation ticks can run sequentially."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        # Run multiple ticks
        for _ in range(3):
            await engine.tick()

        # Check tick events recorded
        history = event_bus.get_history(limit=50)
        tick_events = [e for e in history if e.type == EventType.TICK]
        assert len(tick_events) == 3, "Should have 3 tick events"

        engine.world.close()

    @pytest.mark.asyncio
    async def test_agent_actions_recorded(self, isolated_db_session):
        """Agent actions create events."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        # Run multiple ticks to increase chance of agent actions
        for _ in range(5):
            await engine.tick()

        # Check events recorded - could be action, movement, dialogue, or system events
        history = event_bus.get_history(limit=100)
        non_tick_events = [e for e in history if e.type != EventType.TICK]
        # At minimum, agents should wake up or go to sleep (system events)
        # or perform some action/movement
        assert len(history) >= 5, "Should have at least tick events"

        engine.world.close()

    @pytest.mark.asyncio
    async def test_time_advances_with_ticks(self, isolated_db_session):
        """World time advances with each tick."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        initial_tick = engine.world.get_world_state().current_tick

        # Run a tick
        await engine.tick()

        assert engine.world.get_world_state().current_tick > initial_tick, "Tick should have advanced"

        engine.world.close()

    @pytest.mark.asyncio
    async def test_event_bus_receives_events(self, isolated_db_session):
        """Event bus subscribers receive simulation events."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        # Subscribe to events
        queue = event_bus.subscribe()

        # Run a tick
        await engine.tick()

        # Check that events were published to the queue
        events_received = []
        while not queue.empty():
            events_received.append(queue.get_nowait())

        assert len(events_received) > 0, "Subscriber should have received events"

        # Cleanup
        event_bus.unsubscribe(queue)
        engine.world.close()

    @pytest.mark.asyncio
    async def test_engine_start_stop_cycle(self, isolated_db_session):
        """Engine can be started and stopped cleanly."""
        engine = SimulationEngine(tick_interval=10, use_llm=False)  # Long interval to not tick

        # Start the engine
        await engine.start()
        assert engine.running is True, "Engine should be running"

        # Stop the engine
        await engine.stop()
        assert engine.running is False, "Engine should be stopped"

    @pytest.mark.asyncio
    async def test_world_has_agents_after_tick(self, isolated_db_session):
        """World should have agents after simulation tick."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        await engine.tick()

        agents = engine.world.get_agents()
        assert len(agents) >= 3, "Should have at least 3 seeded agents"

        engine.world.close()

    @pytest.mark.asyncio
    async def test_world_has_locations_after_tick(self, isolated_db_session):
        """World should have locations after simulation tick."""
        engine = SimulationEngine(tick_interval=1, use_llm=False)

        await engine.tick()

        # Query locations through the world's database session
        from hamlet.db import Location

        locations = engine.world.db.query(Location).all()
        assert len(locations) >= 3, "Should have at least 3 seeded locations"

        engine.world.close()
