"""Faction type definitions and constants."""

from enum import Enum


class FactionType(str, Enum):
    """Types of factions that can form."""

    GUILD = "guild"  # Trade/craft-based organization
    POLITICAL = "political"  # Power/governance focused
    SOCIAL = "social"  # Friendship/community based
    RELIGIOUS = "religious"  # Belief/philosophy based
    RIVALRY = "rivalry"  # Opposition to another faction
    ALLIANCE = "alliance"  # Temporary coalition


class FactionStatus(str, Enum):
    """Status of a faction."""

    FORMING = "forming"  # Just created, recruiting
    ACTIVE = "active"  # Fully operational
    STRUGGLING = "struggling"  # Low resources or members
    DISBANDED = "disbanded"  # No longer active


class FactionRole(str, Enum):
    """Roles within a faction."""

    FOUNDER = "founder"  # Created the faction
    LEADER = "leader"  # Current leader (may not be founder)
    OFFICER = "officer"  # Has some authority
    MEMBER = "member"  # Regular member
    RECRUIT = "recruit"  # New member on probation
    OUTCAST = "outcast"  # Former member who was expelled


class FactionRelationType(str, Enum):
    """Types of relationships between factions."""

    ALLY = "ally"  # Friendly, cooperative
    NEUTRAL = "neutral"  # No strong relationship
    COMPETITOR = "competitor"  # Competing for same goals
    ENEMY = "enemy"  # Active hostility


# Minimum members for faction to be considered active
MIN_ACTIVE_MEMBERS = 2

# Maximum factions an agent can belong to
MAX_MEMBERSHIPS = 2

# Loyalty thresholds
LOYALTY_THRESHOLD_OFFICER = 75  # Required loyalty to become officer
LOYALTY_THRESHOLD_LEADER = 90  # Required loyalty to become leader
LOYALTY_MINIMUM = 20  # Below this, agent may leave

# Trait to faction type preferences
TRAIT_FACTION_PREFERENCES: dict[str, list[FactionType]] = {
    "ambition": [FactionType.POLITICAL, FactionType.GUILD],
    "empathy": [FactionType.SOCIAL, FactionType.RELIGIOUS],
    "curiosity": [FactionType.GUILD, FactionType.ALLIANCE],
    "charm": [FactionType.SOCIAL, FactionType.POLITICAL],
    "courage": [FactionType.RIVALRY, FactionType.ALLIANCE],
    "integrity": [FactionType.RELIGIOUS, FactionType.GUILD],
}

# Faction goal templates
FACTION_GOAL_TEMPLATES: dict[FactionType, list[str]] = {
    FactionType.GUILD: [
        "Establish a monopoly on {trade}",
        "Train new apprentices in {skill}",
        "Increase wealth through trade",
    ],
    FactionType.POLITICAL: [
        "Gain influence in the village council",
        "Place a member in a position of power",
        "Shape village policy on {issue}",
    ],
    FactionType.SOCIAL: [
        "Organize a community event",
        "Support members in need",
        "Strengthen bonds between members",
    ],
    FactionType.RELIGIOUS: [
        "Spread our beliefs to others",
        "Build a gathering place",
        "Maintain traditional practices",
    ],
    FactionType.RIVALRY: [
        "Oppose {enemy_faction}",
        "Prove our superiority",
        "Protect members from {threat}",
    ],
    FactionType.ALLIANCE: [
        "Achieve {shared_goal}",
        "Defend against common threat",
        "Combine resources for mutual benefit",
    ],
}
