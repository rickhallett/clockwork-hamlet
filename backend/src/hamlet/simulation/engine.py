"""Simulation engine - the core tick loop."""

import asyncio
import logging
import random
import time

from hamlet.config import settings
from hamlet.db import Agent, Event
from hamlet.simulation.dramatic import (
    check_random_village_event,
    generate_conflict_escalation_dialogue,
    generate_romance_dialogue,
    generate_secret_reaction,
    process_conflict_aftermath,
    process_romance_aftermath,
)
from hamlet.simulation.events import EventType, event_bus
from hamlet.simulation.greetings import generate_arrival_comment
from hamlet.simulation.idle import IdleBehavior, get_idle_behavior
from hamlet.simulation.world import AgentPerception, World

logger = logging.getLogger(__name__)


def format_object_name(obj_id: str) -> str:
    """Convert object ID to readable name: mysterious_portrait -> mysterious portrait."""
    return obj_id.replace("_", " ")


class SimulationEngine:
    """The core simulation engine that runs the tick loop."""

    def __init__(self, tick_interval: float | None = None, use_llm: bool | None = None):
        self.tick_interval = tick_interval or settings.tick_interval_seconds
        self.running = False
        self.world = World(event_bus)
        self._task: asyncio.Task | None = None

        # Use LLM if API key is configured, unless explicitly disabled
        if use_llm is None:
            self.use_llm = bool(settings.anthropic_api_key)
        else:
            self.use_llm = use_llm

        if self.use_llm:
            logger.info("LLM decision-making enabled")
        else:
            logger.info("LLM disabled - using random actions")

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

        # 6. Check for village-wide dramatic events (LIFE-29)
        await self._check_village_events(agents, hour, day)

        # 7. Commit all changes
        self.world.commit()

        # 8. Log agent states
        for agent in agents:
            logger.debug(
                f"  {agent.name}: hunger={agent.hunger:.1f}, "
                f"energy={agent.energy:.1f}, social={agent.social:.1f}, "
                f"state={agent.state}"
            )

    async def _process_agent(self, agent: Agent) -> None:
        """Process a single agent's turn."""
        if self.use_llm:
            await self._process_agent_llm(agent)
        else:
            await self._process_agent_random(agent)

    async def _process_agent_llm(self, agent: Agent) -> None:
        """Process agent turn using LLM decision-making."""
        # Lazy imports to avoid circular dependency
        from hamlet.actions import execute_action
        from hamlet.llm.agent import decide_action

        try:
            # LLM decides action
            action = decide_action(agent, self.world)

            # Execute the action through the action system
            result = execute_action(action, self.world)

            if result.success:
                logger.info(f"  {agent.name}: {result.message}")
                # Publish to event bus for SSE streaming
                await self.world.publish_event(
                    EventType.ACTION,
                    result.message,
                    actors=[agent.id],
                    location_id=agent.location_id,
                )
            else:
                logger.debug(f"  {agent.name} action failed: {result.message}")

        except Exception as e:
            logger.error(f"LLM decision failed for {agent.name}: {e}")
            # Fall back to random action on LLM failure
            await self._process_agent_random(agent)

    async def _process_agent_random(self, agent: Agent) -> None:
        """Process agent turn using random actions (fallback)."""
        perception = self.world.get_agent_perception(agent)
        action = self._choose_random_action(agent, perception)

        if action:
            await self._execute_action(agent, action)
        else:
            # No action chosen - do an idle behavior instead
            await self._do_idle_behavior(agent, perception)

    def _choose_random_action(self, agent: Agent, perception: AgentPerception) -> dict | None:
        """Choose a random action for the agent based on needs and opportunities."""

        choices = []
        weights = []  # Higher weight = more likely

        # Movement - can move to connected locations
        if agent.location_id:
            location = self.world.get_location(agent.location_id)
            if location:
                for conn in location.connections_list:
                    choices.append({"type": "move", "target": conn})
                    weights.append(1)

        # Social interactions with nearby agents
        for other_name in perception.nearby_agents:
            # Greet (light social)
            choices.append({"type": "greet", "target": other_name})
            weights.append(2 if agent.social < 5 else 1)

            # Talk (deeper social, satisfies social need more)
            topic = random.choice(["the weather", "village news", "their day", "old times", "local rumors"])
            choices.append({"type": "talk", "target": other_name, "topic": topic})
            weights.append(3 if agent.social < 5 else 1)

            # Gossip (spreads information, risky)
            choices.append({"type": "gossip", "target": other_name})
            weights.append(1)

            # Help (builds relationships)
            choices.append({"type": "help", "target": other_name})
            weights.append(1)

        # Solo actions - examine objects
        for obj in perception.nearby_objects:
            choices.append({"type": "examine", "target": obj})
            weights.append(1)

        # Work action (if at appropriate location)
        work_locations = {"bakery": "baking", "blacksmith": "smithing", "inn": "innkeeping",
                         "tavern": "serving", "church": "praying", "garden": "gardening"}
        if agent.location_id in work_locations:
            choices.append({"type": "work", "job": work_locations[agent.location_id]})
            weights.append(2)

        # Investigate (for curious agents or when something is amiss)
        if agent.location_id:
            mysteries = ["strange noises", "unusual footprints", "mysterious lights", "missing items"]
            choices.append({"type": "investigate", "mystery": random.choice(mysteries)})
            weights.append(1)

        # Wait/rest
        choices.append({"type": "wait"})
        weights.append(1 if agent.energy > 5 else 3)

        # 20% chance to do nothing (adds variety)
        if random.random() < 0.2:
            return None

        if not choices:
            return None

        # Weighted random selection
        return random.choices(choices, weights=weights, k=1)[0]

    async def _execute_action(self, agent: Agent, action: dict) -> None:
        """Execute an action for an agent."""
        action_type = action.get("type")
        target = action.get("target")

        if action_type == "move":
            await self._do_move(agent, target)
        elif action_type == "greet":
            await self._do_greet(agent, target)
        elif action_type == "talk":
            await self._do_talk(agent, target, action.get("topic", "various things"))
        elif action_type == "gossip":
            await self._do_gossip(agent, target)
        elif action_type == "help":
            await self._do_help(agent, target)
        elif action_type == "examine":
            await self._do_examine(agent, target)
        elif action_type == "work":
            await self._do_work(agent, action.get("job", "working"))
        elif action_type == "investigate":
            await self._do_investigate(agent, action.get("mystery", "something"))
        elif action_type == "wait":
            logger.debug(f"  {agent.name} rests")

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

            # Check for other agents and potentially generate a greeting
            others = self.world.get_agents_at_location(destination_id)
            others = [a for a in others if a.id != agent.id]

            if others:
                perception = self.world.get_agent_perception(agent)
                comment = generate_arrival_comment(agent, others, perception)

                if comment:
                    logger.info(f"  {agent.name} greets: {comment}")

                    await self.world.publish_event(
                        EventType.DIALOGUE,
                        comment,
                        actors=[agent.id],
                        location_id=destination_id,
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

    async def _do_examine(self, agent: Agent, object_id: str) -> None:
        """Agent examines an object."""
        object_name = format_object_name(object_id)
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

    async def _do_talk(self, agent: Agent, target_name: str, topic: str) -> None:
        """Agent talks with another agent."""
        logger.info(f"  {agent.name} talked with {target_name} about {topic}")

        # Increase social satisfaction
        agent.social = min(10, agent.social + 1)

        await self.world.publish_event(
            EventType.DIALOGUE,
            f"{agent.name} chatted with {target_name} about {topic}",
            actors=[agent.id],
            location_id=agent.location_id,
            detail=f'{agent.name} and {target_name} discussed {topic}',
        )

        self._record_event(
            "dialogue",
            f"{agent.name} chatted with {target_name} about {topic}",
            [agent.id],
            agent.location_id,
            f'{agent.name} and {target_name} discussed {topic}',
            significance=2,
        )

    async def _do_gossip(self, agent: Agent, target_name: str) -> None:
        """Agent gossips with another agent."""
        # Pick a random third party to gossip about
        all_agents = self.world.get_agents()
        others = [a for a in all_agents if a.name != agent.name and a.name != target_name]
        if not others:
            return

        subject = random.choice(others)
        rumors = [
            f"acting strangely lately",
            f"seen near the forest at odd hours",
            f"hiding something",
            f"been very secretive",
            f"spending a lot of time alone",
        ]
        rumor = random.choice(rumors)

        logger.info(f"  {agent.name} gossiped with {target_name} about {subject.name}")

        await self.world.publish_event(
            EventType.DIALOGUE,
            f"{agent.name} shared gossip with {target_name}",
            actors=[agent.id],
            location_id=agent.location_id,
            detail=f'{agent.name} whispered to {target_name}: "Have you heard? {subject.name} has been {rumor}..."',
        )

        self._record_event(
            "dialogue",
            f"{agent.name} shared gossip about {subject.name} with {target_name}",
            [agent.id],
            agent.location_id,
            significance=2,
        )

    async def _do_help(self, agent: Agent, target_name: str) -> None:
        """Agent helps another agent."""
        tasks = ["carry supplies", "with a task", "tidy up", "prepare for the day"]
        task = random.choice(tasks)

        logger.info(f"  {agent.name} helped {target_name} {task}")

        await self.world.publish_event(
            EventType.ACTION,
            f"{agent.name} helped {target_name} {task}",
            actors=[agent.id],
            location_id=agent.location_id,
        )

        self._record_event(
            "action",
            f"{agent.name} helped {target_name} {task}",
            [agent.id],
            agent.location_id,
            significance=2,
        )

    async def _do_work(self, agent: Agent, job_type: str) -> None:
        """Agent performs work."""
        agent.energy = max(0, agent.energy - 0.5)

        logger.info(f"  {agent.name} is {job_type}")

        await self.world.publish_event(
            EventType.ACTION,
            f"{agent.name} is busy {job_type}",
            actors=[agent.id],
            location_id=agent.location_id,
        )

        self._record_event(
            "action",
            f"{agent.name} worked on {job_type}",
            [agent.id],
            agent.location_id,
        )

    async def _do_investigate(self, agent: Agent, mystery: str) -> None:
        """Agent investigates something mysterious."""
        logger.info(f"  {agent.name} investigated {mystery}")

        outcomes = [
            f"but found nothing unusual",
            f"and noticed something odd",
            f"and grew more curious",
            f"but was interrupted",
        ]
        outcome = random.choice(outcomes)

        await self.world.publish_event(
            EventType.ACTION,
            f"{agent.name} investigated {mystery} {outcome}",
            actors=[agent.id],
            location_id=agent.location_id,
        )

        self._record_event(
            "action",
            f"{agent.name} investigated {mystery}",
            [agent.id],
            agent.location_id,
            significance=2,
        )

    async def _do_idle_behavior(self, agent: Agent, perception: AgentPerception) -> None:
        """Agent does an idle behavior - thoughts, observations, small actions."""
        behavior = get_idle_behavior(agent, perception)

        if behavior is None:
            # Truly do nothing (rare)
            logger.debug(f"  {agent.name} does nothing")
            return

        logger.debug(f"  {agent.name} idle: {behavior.content}")

        # Map behavior type to event type
        event_type = EventType.ACTION
        if behavior.type == "thought":
            event_type = EventType.SYSTEM  # Internal thoughts
        elif behavior.type == "observation":
            event_type = EventType.DISCOVERY

        await self.world.publish_event(
            event_type,
            behavior.content,
            actors=[agent.id],
            location_id=agent.location_id,
            significance=behavior.significance,
        )

    async def _check_village_events(
        self, agents: list[Agent], current_hour: float, current_day: int
    ) -> None:
        """Check for and process village-wide dramatic events (LIFE-29)."""
        village_event = check_random_village_event(
            self.world.db, agents, current_hour, current_day
        )

        if village_event:
            logger.info(f"  [VILLAGE EVENT] {village_event.description}")

            await self.world.publish_event(
                EventType.SYSTEM,
                village_event.description,
                actors=village_event.affected_agents[:5],  # Limit actor list
                location_id=village_event.location_id,
                significance=village_event.significance,
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
