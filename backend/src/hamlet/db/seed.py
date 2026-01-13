"""Database seeding script."""

import json

from hamlet.db.connection import SessionLocal, engine
from hamlet.db.models import Agent, Base, Location, Relationship, WorldState


def seed_locations(db) -> list[Location]:
    """Create initial locations."""
    locations = [
        Location(
            id="town_square",
            name="Town Square",
            description="The heart of the village, with a weathered fountain and wooden benches.",
            connections=json.dumps(["bakery", "tavern", "church"]),
            objects=json.dumps(["fountain", "bench", "notice_board"]),
            capacity=20,
        ),
        Location(
            id="bakery",
            name="The Warm Hearth Bakery",
            description="A cozy bakery filled with the aroma of fresh bread and pastries.",
            connections=json.dumps(["town_square"]),
            objects=json.dumps(["counter", "oven", "bread_basket"]),
            capacity=8,
        ),
        Location(
            id="tavern",
            name="The Rusty Tankard",
            description="A dimly lit tavern where villagers gather to share stories and ale.",
            connections=json.dumps(["town_square"]),
            objects=json.dumps(["bar", "fireplace", "dartboard", "tables"]),
            capacity=15,
        ),
    ]

    for loc in locations:
        db.add(loc)

    return locations


def seed_agents(db) -> list[Agent]:
    """Create initial agents."""
    agents = [
        Agent(
            id="agnes",
            name="Agnes Thornbury",
            personality_prompt=(
                "Agnes is the village baker, a sharp-tongued woman in her 50s with an even sharper memory. "
                "She knows everyone's business and isn't afraid to share it. Despite her gossipy nature, "
                "she has a warm heart and genuinely cares about the village. She's fiercely proud of her "
                "sourdough and considers baking an art form."
            ),
            traits=json.dumps(
                {
                    "curiosity": 8,
                    "empathy": 6,
                    "ambition": 4,
                    "discretion": 2,
                    "energy": 7,
                    "courage": 5,
                    "charm": 6,
                    "perception": 8,
                }
            ),
            location_id="bakery",
            inventory=json.dumps(["rolling_pin", "bread_loaf"]),
            mood=json.dumps({"happiness": 6, "energy": 7}),
            state="idle",
            hunger=2.0,
            energy=8.0,
            social=6.0,
        ),
        Agent(
            id="bob",
            name="Bob Millwright",
            personality_prompt=(
                "Bob is a gentle farmer in his 40s who tends to the village's main vegetable garden. "
                "He's somewhat melancholic after his wife passed three years ago, but finds solace in "
                "his work. He enters his prized pumpkins in the annual harvest festival and takes "
                "the competition very seriously. He's kind but quiet, often lost in thought."
            ),
            traits=json.dumps(
                {
                    "curiosity": 4,
                    "empathy": 8,
                    "ambition": 3,
                    "discretion": 7,
                    "energy": 5,
                    "courage": 4,
                    "charm": 5,
                    "perception": 6,
                }
            ),
            location_id="town_square",
            inventory=json.dumps(["garden_trowel"]),
            mood=json.dumps({"happiness": 4, "energy": 5}),
            state="idle",
            hunger=3.0,
            energy=6.0,
            social=4.0,
        ),
        Agent(
            id="martha",
            name="Martha Hendricks",
            personality_prompt=(
                "Martha is the mayor's wife, a refined woman in her 60s who takes her social standing "
                "seriously. She organizes village events and considers herself the arbiter of proper "
                "behavior. Beneath her prim exterior, she harbors a secret fondness for adventure novels "
                "and occasionally wishes her life were more exciting. She's Agnes's oldest friend, though "
                "they often bicker."
            ),
            traits=json.dumps(
                {
                    "curiosity": 6,
                    "empathy": 5,
                    "ambition": 7,
                    "discretion": 6,
                    "energy": 6,
                    "courage": 3,
                    "charm": 8,
                    "perception": 7,
                }
            ),
            location_id="town_square",
            inventory=json.dumps(["parasol", "handkerchief"]),
            mood=json.dumps({"happiness": 5, "energy": 6}),
            state="idle",
            hunger=1.0,
            energy=7.0,
            social=7.0,
        ),
    ]

    for agent in agents:
        db.add(agent)

    return agents


def seed_relationships(db, agents: list[Agent]) -> None:
    """Create initial relationships between agents."""
    relationships = [
        # Agnes and Martha are old friends
        Relationship(
            agent_id="agnes",
            target_id="martha",
            type="friend",
            score=7,
            history=json.dumps(["Known each other for 30 years", "Bicker often but deeply care"]),
        ),
        Relationship(
            agent_id="martha",
            target_id="agnes",
            type="friend",
            score=6,
            history=json.dumps(["Best friend since childhood", "Sometimes finds Agnes too nosy"]),
        ),
        # Agnes knows Bob as a customer
        Relationship(
            agent_id="agnes",
            target_id="bob",
            type="acquaintance",
            score=3,
            history=json.dumps(["Regular bread customer"]),
        ),
        Relationship(
            agent_id="bob",
            target_id="agnes",
            type="acquaintance",
            score=4,
            history=json.dumps(["Buys bread from her bakery"]),
        ),
        # Martha and Bob are polite acquaintances
        Relationship(
            agent_id="martha",
            target_id="bob",
            type="acquaintance",
            score=2,
            history=json.dumps(["Sees him at village events"]),
        ),
        Relationship(
            agent_id="bob",
            target_id="martha",
            type="acquaintance",
            score=2,
            history=json.dumps(["The mayor's wife"]),
        ),
    ]

    for rel in relationships:
        db.add(rel)


def seed_world_state(db) -> WorldState:
    """Create initial world state."""
    world = WorldState(
        id=1,
        current_tick=0,
        current_day=1,
        current_hour=6.0,
        season="spring",
        weather="clear",
    )
    db.add(world)
    return world


def seed_database() -> None:
    """Seed the database with initial data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Agent).first()
        if existing:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Seed in order (respecting foreign keys)
        locations = seed_locations(db)
        print(f"  Created {len(locations)} locations")

        agents = seed_agents(db)
        print(f"  Created {len(agents)} agents")

        seed_relationships(db, agents)
        print("  Created initial relationships")

        seed_world_state(db)
        print("  Created world state")

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


def reset_database() -> None:
    """Drop all tables and reseed."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    seed_database()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        seed_database()
