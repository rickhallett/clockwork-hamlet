"""Simulation engine - the core tick loop."""

import asyncio
import logging
import random
import time

from hamlet.config import settings
from hamlet.db import Agent, Event
from hamlet.simulation.events import EventType, event_bus
from hamlet.simulation.world import AgentPerception, World

logger = logging.getLogger(__name__)


class SimulationEngine:
    """The core simulation engine that runs the tick loop."""

    def __init__(self, tick_interval: float | None = None):
        self.tick_interval = tick_interval or settings.tick_interval_seconds
        self.running = False
        self.world = World(event_bus)
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the simulation loop."""
        if self.running:
            logger.warning("Simulation already running")
            return

        self.running = True
        logger.info("Starting simulation engine")
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the simulation loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.world.close()
        logger.info("Simulation engine stopped")

    async def _run_loop(self) -> None:
        """The main simulation loop."""
        while self.running:
            try:
                await self.tick()
                await asyncio.sleep(self.tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def tick(self) -> None:
        """Execute a single simulation tick."""
        # 1. Advance world time
        tick, day, hour = self.world.advance_time(minutes=30)
        logger.info(f"[Tick {tick}] Day {day}, {hour:.1f}:00")

        # 2. Publish tick event
        await self.world.publish_event(
            EventType.TICK,
            f"Tick {tick}: Day {day}, {int(hour):02d}:{int((hour % 1) * 60):02d}",
            significance=1,
        )

        # 3. Handle day/night transitions
        woken = self.world.wake_sleeping_agents()
        for agent in woken:
            logger.info(f"  {agent.name} woke up")
            await self.world.publish_event(
                EventType.SYSTEM,
                f"{agent.name} woke up",
                actors=[agent.id],
                location_id=agent.location_id,
            )

        sleeping = self.world.put_agents_to_sleep()
        for agent in sleeping:
            logger.info(f"  {agent.name} went to sleep")
            await self.world.publish_event(
                EventType.SYSTEM,
                f"{agent.name} went to sleep",
                actors=[agent.id],
                location_id=agent.location_id,
            )

        # 4. Update agent needs
        agents = self.world.get_agents()
        for agent in agents:
            self.world.update_agent_needs(agent, hours_passed=0.5)

        # 5. Process active agents (not sleeping)
        active_agents = [a for a in agents if a.state != "sleeping"]

        for agent in active_agents:
            await self._process_agent(agent)

        # 6. Commit all changes
        self.world.commit()

        # 7. Log agent states
        for agent in agents:
            logger.debug(
                f"  {agent.name}: hunger={agent.hunger:.1f}, "
                f"energy={agent.energy:.1f}, social={agent.social:.1f}, "
                f"state={agent.state}"
            )

    async def _process_agent(self, agent: Agent) -> None:
        """Process a single agent's turn."""
        # Get perception
        perception = self.world.get_agent_perception(agent)

        # For now, random actions (LLM integration comes in Phase 4)
        action = self._choose_random_action(agent, perception)

        if action:
            await self._execute_action(agent, action)

    def _choose_random_action(self, agent: Agent, perception: AgentPerception) -> dict | None:
        """Choose a random action for the agent. Placeholder for LLM."""

        # Simple random behavior
        choices = []

        # Can move to connected locations
        if agent.location_id:
            location = self.world.get_location(agent.location_id)
            if location:
                for conn in location.connections_list:
                    choices.append({"type": "move", "target": conn})

        # Can interact with nearby agents
        for other_name in perception.nearby_agents:
            choices.append({"type": "greet", "target": other_name})

        # Can examine objects
        for obj in perception.nearby_objects:
            choices.append({"type": "examine", "target": obj})

        # Can wait
        choices.append({"type": "wait"})

        # 30% chance to do nothing (adds variety)
        if random.random() < 0.3:
            return None

        return random.choice(choices) if choices else None

    async def _execute_action(self, agent: Agent, action: dict) -> None:
        """Execute an action for an agent."""
        action_type = action.get("type")
        target = action.get("target")

        if action_type == "move":
            await self._do_move(agent, target)
        elif action_type == "greet":
            await self._do_greet(agent, target)
        elif action_type == "examine":
            await self._do_examine(agent, target)
        elif action_type == "wait":
            logger.debug(f"  {agent.name} waits")

    async def _do_move(self, agent: Agent, destination_id: str) -> None:
        """Move an agent to a new location."""
        new_location = self.world.get_location(destination_id)

        if new_location:
            agent.location_id = destination_id
            logger.info(f"  {agent.name} moved to {new_location.name}")

            await self.world.publish_event(
                EventType.MOVEMENT,
                f"{agent.name} moved to {new_location.name}",
                actors=[agent.id],
                location_id=destination_id,
            )

            # Store event in database
            self._record_event(
                "movement",
                f"{agent.name} arrived at {new_location.name}",
                [agent.id],
                destination_id,
            )

    async def _do_greet(self, agent: Agent, target_name: str) -> None:
        """Agent greets another agent."""
        logger.info(f"  {agent.name} greeted {target_name}")

        await self.world.publish_event(
            EventType.DIALOGUE,
            f"{agent.name} greeted {target_name}",
            actors=[agent.id],
            location_id=agent.location_id,
            detail=f'{agent.name}: "Hello, {target_name}!"',
        )

        self._record_event(
            "dialogue",
            f"{agent.name} greeted {target_name}",
            [agent.id],
            agent.location_id,
            f'{agent.name}: "Hello, {target_name}!"',
        )

    async def _do_examine(self, agent: Agent, object_name: str) -> None:
        """Agent examines an object."""
        logger.info(f"  {agent.name} examined {object_name}")

        await self.world.publish_event(
            EventType.ACTION,
            f"{agent.name} examined the {object_name}",
            actors=[agent.id],
            location_id=agent.location_id,
        )

        self._record_event(
            "action",
            f"{agent.name} examined the {object_name}",
            [agent.id],
            agent.location_id,
        )

    def _record_event(
        self,
        event_type: str,
        summary: str,
        actors: list[str],
        location_id: str | None,
        detail: str | None = None,
        significance: int = 1,
    ) -> None:
        """Record an event to the database."""
        import json

        event = Event(
            timestamp=int(time.time()),
            type=event_type,
            actors=json.dumps(actors),
            location_id=location_id,
            summary=summary,
            detail=detail,
            significance=significance,
        )
        self.world.db.add(event)


async def run_simulation(num_ticks: int = 10, tick_interval: float = 0.1) -> None:
    """Run the simulation for a specified number of ticks."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    engine = SimulationEngine(tick_interval=tick_interval)

    logger.info(f"Running simulation for {num_ticks} ticks...")
    logger.info("=" * 50)

    for _ in range(num_ticks):
        await engine.tick()

    engine.world.close()
    logger.info("=" * 50)
    logger.info("Simulation complete!")


def main():
    """Entry point for running simulation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the Clockwork Hamlet simulation")
    parser.add_argument("--ticks", type=int, default=10, help="Number of ticks to run")
    parser.add_argument("--interval", type=float, default=0.1, help="Seconds between ticks")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for decisions (Phase 4)")
    args = parser.parse_args()

    asyncio.run(run_simulation(num_ticks=args.ticks, tick_interval=args.interval))


if __name__ == "__main__":
    main()
