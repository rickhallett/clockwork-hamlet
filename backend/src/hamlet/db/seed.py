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
            connections=json.dumps(["bakery", "tavern", "church", "mayors_house", "blacksmith"]),
            objects=json.dumps(["fountain", "bench", "notice_board", "old_clock_tower"]),
            capacity=20,
        ),
        Location(
            id="bakery",
            name="The Warm Hearth Bakery",
            description="A cozy bakery filled with the aroma of fresh bread and pastries.",
            connections=json.dumps(["town_square"]),
            objects=json.dumps(["counter", "oven", "bread_basket", "secret_recipe_box"]),
            capacity=8,
        ),
        Location(
            id="tavern",
            name="The Rusty Tankard",
            description="A dimly lit tavern where villagers gather to share stories and ale.",
            connections=json.dumps(["town_square", "inn"]),
            objects=json.dumps(["bar", "fireplace", "dartboard", "tables", "mysterious_portrait"]),
            capacity=15,
        ),
        Location(
            id="church",
            name="St. Aldhelm's Church",
            description="A modest stone church with beautiful stained glass windows and a peaceful cemetery behind.",
            connections=json.dumps(["town_square", "cemetery"]),
            objects=json.dumps(["altar", "pews", "confession_booth", "ancient_tome"]),
            capacity=30,
        ),
        Location(
            id="cemetery",
            name="The Old Cemetery",
            description="A quiet resting place for the village's departed, shadowed by ancient oak trees.",
            connections=json.dumps(["church"]),
            objects=json.dumps(["gravestones", "old_mausoleum", "willow_tree", "mysterious_grave"]),
            capacity=10,
        ),
        Location(
            id="mayors_house",
            name="The Mayor's Residence",
            description="An imposing two-story house with manicured gardens and the village's only weathervane.",
            connections=json.dumps(["town_square", "garden"]),
            objects=json.dumps(["study", "dining_table", "grandfather_clock", "locked_cabinet"]),
            capacity=10,
        ),
        Location(
            id="garden",
            name="Village Garden",
            description="A communal garden where Bob tends his prized vegetables and others grow herbs and flowers.",
            connections=json.dumps(["mayors_house", "farm"]),
            objects=json.dumps(["vegetable_patch", "pumpkin_patch", "tool_shed", "scarecrow"]),
            capacity=12,
        ),
        Location(
            id="farm",
            name="Millwright Farm",
            description="A modest farm on the village outskirts with fields of wheat and a red barn.",
            connections=json.dumps(["garden", "forest_edge"]),
            objects=json.dumps(["barn", "chicken_coop", "well", "haystack"]),
            capacity=15,
        ),
        Location(
            id="blacksmith",
            name="The Anvil & Ember",
            description="A hot, smoky workshop where metal is shaped into tools, horseshoes, and occasionally weapons.",
            connections=json.dumps(["town_square"]),
            objects=json.dumps(["forge", "anvil", "weapons_rack", "mysterious_sword"]),
            capacity=6,
        ),
        Location(
            id="inn",
            name="The Weary Traveler Inn",
            description="A comfortable inn with rooms for travelers and a shared dining hall.",
            connections=json.dumps(["tavern"]),
            objects=json.dumps(["front_desk", "guest_ledger", "room_keys", "lost_and_found"]),
            capacity=20,
        ),
        Location(
            id="forest_edge",
            name="Forest Edge",
            description="The boundary between civilization and the dark, whispering woods. Strange lights are sometimes seen deeper within.",
            connections=json.dumps(["farm"]),
            objects=json.dumps(["old_signpost", "mushroom_ring", "hollow_tree", "animal_tracks"]),
            capacity=8,
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
        Agent(
            id="edmund",
            name="Edmund Blackwood",
            personality_prompt=(
                "Edmund is the village blacksmith, a burly man in his 40s with a mysterious past. "
                "He arrived in the hamlet five years ago and rarely speaks of where he came from. "
                "He's skilled with metal and fire, but sometimes late at night, he can be seen forging "
                "something in secret. He's gruff but fair, and has a soft spot for children."
            ),
            traits=json.dumps(
                {
                    "curiosity": 3,
                    "empathy": 5,
                    "ambition": 4,
                    "discretion": 9,
                    "energy": 8,
                    "courage": 8,
                    "charm": 3,
                    "perception": 6,
                }
            ),
            location_id="blacksmith",
            inventory=json.dumps(["hammer", "tongs", "mysterious_key"]),
            mood=json.dumps({"happiness": 4, "energy": 7}),
            state="idle",
            hunger=4.0,
            energy=7.0,
            social=2.0,
        ),
        Agent(
            id="rosalind",
            name="Rosalind Fairweather",
            personality_prompt=(
                "Rosalind is the young innkeeper, a cheerful woman in her late 20s who inherited "
                "The Weary Traveler from her late uncle. She loves hearing travelers' stories and "
                "dreams of adventure beyond the village. She's observant and keeps a journal of "
                "interesting guests and their tales. She has a secret crush on Edmund the blacksmith."
            ),
            traits=json.dumps(
                {
                    "curiosity": 9,
                    "empathy": 7,
                    "ambition": 6,
                    "discretion": 4,
                    "energy": 8,
                    "courage": 5,
                    "charm": 8,
                    "perception": 7,
                }
            ),
            location_id="inn",
            inventory=json.dumps(["room_key", "journal", "travelers_map"]),
            mood=json.dumps({"happiness": 7, "energy": 8}),
            state="idle",
            hunger=2.0,
            energy=8.0,
            social=8.0,
        ),
        Agent(
            id="father_cornelius",
            name="Father Cornelius",
            personality_prompt=(
                "Father Cornelius is the elderly village priest, a kind soul in his 70s who has "
                "served the hamlet for over 40 years. He knows many secrets from confessions but "
                "guards them carefully. He's noticed strange occurrences lately and worries about "
                "the old legends of the forest. He speaks in gentle homilies and loves tending the church garden."
            ),
            traits=json.dumps(
                {
                    "curiosity": 6,
                    "empathy": 9,
                    "ambition": 2,
                    "discretion": 10,
                    "energy": 3,
                    "courage": 6,
                    "charm": 7,
                    "perception": 8,
                }
            ),
            location_id="church",
            inventory=json.dumps(["prayer_beads", "bible", "holy_water"]),
            mood=json.dumps({"happiness": 6, "energy": 4}),
            state="idle",
            hunger=2.0,
            energy=4.0,
            social=5.0,
        ),
        Agent(
            id="theodore",
            name="Theodore Hendricks",
            personality_prompt=(
                "Theodore is the village mayor, Martha's husband, a portly man in his 60s who "
                "loves his position but is secretly incompetent. He delegates most work to others "
                "and takes credit for successes. He's terrified of the village discovering that "
                "the prize cheese from last year's festival was actually store-bought. He means well but panics easily."
            ),
            traits=json.dumps(
                {
                    "curiosity": 3,
                    "empathy": 4,
                    "ambition": 8,
                    "discretion": 2,
                    "energy": 4,
                    "courage": 2,
                    "charm": 6,
                    "perception": 4,
                }
            ),
            location_id="mayors_house",
            inventory=json.dumps(["mayoral_chain", "pocket_watch", "receipt_from_city"]),
            mood=json.dumps({"happiness": 5, "energy": 4}),
            state="idle",
            hunger=1.0,
            energy=5.0,
            social=6.0,
        ),
        Agent(
            id="eliza",
            name="Eliza Thornbury",
            personality_prompt=(
                "Eliza is Agnes's niece, a spirited young woman of 22 who recently returned to the "
                "village after studying herbalism in the city. She's scientifically minded but open "
                "to old folk wisdom. She's set up a small apothecary in the bakery's back room and "
                "is investigating strange plant growth at the forest edge. She clashes with Father Cornelius "
                "over superstition vs. science."
            ),
            traits=json.dumps(
                {
                    "curiosity": 10,
                    "empathy": 6,
                    "ambition": 7,
                    "discretion": 5,
                    "energy": 9,
                    "courage": 7,
                    "charm": 5,
                    "perception": 8,
                }
            ),
            location_id="bakery",
            inventory=json.dumps(["herb_pouch", "magnifying_glass", "notebook"]),
            mood=json.dumps({"happiness": 7, "energy": 9}),
            state="idle",
            hunger=3.0,
            energy=9.0,
            social=5.0,
        ),
        Agent(
            id="william",
            name="William 'Old Will' Cooper",
            personality_prompt=(
                "Old Will is the village's oldest resident at 82, a retired cooper who now spends "
                "his days at the tavern telling stories. He claims to have seen the 'lights in the forest' "
                "as a boy and knows all the old legends. Most dismiss him as a drunk, but his stories "
                "are surprisingly consistent. He was best friends with Bob's late wife's father."
            ),
            traits=json.dumps(
                {
                    "curiosity": 5,
                    "empathy": 6,
                    "ambition": 1,
                    "discretion": 3,
                    "energy": 2,
                    "courage": 5,
                    "charm": 7,
                    "perception": 7,
                }
            ),
            location_id="tavern",
            inventory=json.dumps(["walking_stick", "old_photograph", "lucky_coin"]),
            mood=json.dumps({"happiness": 5, "energy": 3}),
            state="idle",
            hunger=2.0,
            energy=3.0,
            social=7.0,
        ),
        Agent(
            id="thomas",
            name="Thomas Ashford",
            personality_prompt=(
                "Thomas is the tavern keeper, a jovial man in his 50s who knows how to keep secrets "
                "and pour drinks in equal measure. He's the unofficial information broker of the village - "
                "everyone talks to the bartender. He's secretly in love with Agnes but has never confessed. "
                "He waters down drinks for those who've had too much but never admits it."
            ),
            traits=json.dumps(
                {
                    "curiosity": 7,
                    "empathy": 7,
                    "ambition": 4,
                    "discretion": 8,
                    "energy": 6,
                    "courage": 5,
                    "charm": 9,
                    "perception": 8,
                }
            ),
            location_id="tavern",
            inventory=json.dumps(["bar_towel", "key_ring", "love_letter_draft"]),
            mood=json.dumps({"happiness": 6, "energy": 6}),
            state="idle",
            hunger=2.0,
            energy=6.0,
            social=9.0,
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
        # Agnes and Eliza (aunt and niece)
        Relationship(
            agent_id="agnes",
            target_id="eliza",
            type="family",
            score=8,
            history=json.dumps(["Raised her after her parents passed", "Proud of her education"]),
        ),
        Relationship(
            agent_id="eliza",
            target_id="agnes",
            type="family",
            score=8,
            history=json.dumps(["Aunt Agnes taught her everything", "Sometimes feels smothered"]),
        ),
        # Agnes knows Bob as a customer
        Relationship(
            agent_id="agnes",
            target_id="bob",
            type="acquaintance",
            score=4,
            history=json.dumps(["Regular bread customer", "Feels sorry for him since his wife died"]),
        ),
        Relationship(
            agent_id="bob",
            target_id="agnes",
            type="acquaintance",
            score=4,
            history=json.dumps(["Buys bread from her bakery"]),
        ),
        # Martha and Theodore (married)
        Relationship(
            agent_id="martha",
            target_id="theodore",
            type="spouse",
            score=6,
            history=json.dumps(["Married 35 years", "Loves him despite his flaws"]),
        ),
        Relationship(
            agent_id="theodore",
            target_id="martha",
            type="spouse",
            score=7,
            history=json.dumps(["She runs everything", "Couldn't manage without her"]),
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
        # Old Will and Bob (through Bob's late wife)
        Relationship(
            agent_id="william",
            target_id="bob",
            type="friend",
            score=5,
            history=json.dumps(["Best friend of his late father-in-law", "Shared grief"]),
        ),
        Relationship(
            agent_id="bob",
            target_id="william",
            type="friend",
            score=5,
            history=json.dumps(["Connection to his late wife", "Listens to his stories"]),
        ),
        # Thomas and Agnes (secret love)
        Relationship(
            agent_id="thomas",
            target_id="agnes",
            type="friend",
            score=7,
            history=json.dumps(["Secretly in love with her", "Never confessed"]),
        ),
        Relationship(
            agent_id="agnes",
            target_id="thomas",
            type="friend",
            score=5,
            history=json.dumps(["Good friend and drinking companion", "Oblivious to his feelings"]),
        ),
        # Rosalind and Edmund (unrequited crush)
        Relationship(
            agent_id="rosalind",
            target_id="edmund",
            type="acquaintance",
            score=6,
            history=json.dumps(["Secret crush", "Nervous around him"]),
        ),
        Relationship(
            agent_id="edmund",
            target_id="rosalind",
            type="acquaintance",
            score=3,
            history=json.dumps(["The innkeeper", "Barely notices her"]),
        ),
        # Father Cornelius and Eliza (ideological tension)
        Relationship(
            agent_id="father_cornelius",
            target_id="eliza",
            type="acquaintance",
            score=1,
            history=json.dumps(["Worried about her 'science'", "Thinks she meddles with nature"]),
        ),
        Relationship(
            agent_id="eliza",
            target_id="father_cornelius",
            type="acquaintance",
            score=2,
            history=json.dumps(["Finds him superstitious", "Respects his kindness"]),
        ),
        # Edmund and Theodore (tension)
        Relationship(
            agent_id="edmund",
            target_id="theodore",
            type="acquaintance",
            score=-1,
            history=json.dumps(["Suspicious of the mayor", "Knows he's hiding something"]),
        ),
        Relationship(
            agent_id="theodore",
            target_id="edmund",
            type="acquaintance",
            score=0,
            history=json.dumps(["Afraid of the mysterious blacksmith"]),
        ),
        # Old Will and Father Cornelius (shared history)
        Relationship(
            agent_id="william",
            target_id="father_cornelius",
            type="friend",
            score=6,
            history=json.dumps(["Both remember the old days", "Share knowledge of legends"]),
        ),
        Relationship(
            agent_id="father_cornelius",
            target_id="william",
            type="friend",
            score=5,
            history=json.dumps(["Old friend", "Worries about his drinking"]),
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
