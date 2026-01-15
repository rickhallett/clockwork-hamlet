"""Agent schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TraitsSchema(BaseModel):
    """Agent personality traits."""

    curiosity: int = Field(default=5, ge=1, le=10)
    empathy: int = Field(default=5, ge=1, le=10)
    ambition: int = Field(default=5, ge=1, le=10)
    discretion: int = Field(default=5, ge=1, le=10)
    energy: int = Field(default=5, ge=1, le=10)
    courage: int = Field(default=5, ge=1, le=10)
    charm: int = Field(default=5, ge=1, le=10)
    perception: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_trait_balance(self) -> "TraitsSchema":
        """Validate that trait combinations are realistic."""
        # Check for extreme combinations that would be psychologically inconsistent
        issues = []

        # High empathy + very low discretion + low courage = unstable combination
        if self.empathy >= 9 and self.discretion <= 2 and self.courage <= 2:
            issues.append("High empathy with very low discretion and courage is unstable")

        # Very high ambition + very low energy = contradictory
        if self.ambition >= 9 and self.energy <= 2:
            issues.append("Very high ambition requires at least moderate energy")

        # All traits at extremes (all 1 or all 10) is unrealistic
        trait_values = [
            self.curiosity, self.empathy, self.ambition, self.discretion,
            self.energy, self.courage, self.charm, self.perception
        ]
        if all(v <= 2 for v in trait_values) or all(v >= 9 for v in trait_values):
            issues.append("All traits at extreme values is unrealistic")

        if issues:
            raise ValueError("; ".join(issues))

        return self


class MoodSchema(BaseModel):
    """Agent mood state."""

    happiness: int = Field(default=5, ge=0, le=10)
    energy: int = Field(default=7, ge=0, le=10)


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str
    personality_prompt: str | None = None
    traits: TraitsSchema = Field(default_factory=TraitsSchema)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""

    id: str
    location_id: str | None = None


class AgentResponse(BaseModel):
    """Schema for agent response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    personality_prompt: str | None = None
    traits: dict = {}
    location_id: str | None
    inventory: list[str] = []
    mood: dict = {}
    state: str
    hunger: float = 0.0
    energy: float = 10.0
    social: float = 5.0


class AgentDetail(BaseModel):
    """Schema for detailed agent response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    personality_prompt: str | None
    traits: TraitsSchema
    location_id: str | None
    inventory: list[str]
    mood: MoodSchema
    state: str
    hunger: float
    energy: float
    social: float


# Agent creation schemas for USER-7

class AgentCreateRequest(BaseModel):
    """Request schema for creating a new agent."""

    name: str = Field(..., min_length=2, max_length=50, description="Agent display name")
    personality_prompt: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Character description/backstory"
    )
    traits: TraitsSchema = Field(default_factory=TraitsSchema)
    location_id: str | None = Field(
        default=None,
        description="Starting location ID (defaults to village_square)"
    )
    preset: str | None = Field(
        default=None,
        description="Optional preset name to use as trait base"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name."""
        # Remove leading/trailing whitespace
        v = v.strip()
        # Check for valid characters (letters, spaces, apostrophes, hyphens)
        import re
        if not re.match(r"^[a-zA-Z][a-zA-Z\s'\-]*$", v):
            raise ValueError(
                "Name must start with a letter and contain only letters, "
                "spaces, apostrophes, and hyphens"
            )
        return v

    @field_validator("personality_prompt")
    @classmethod
    def validate_personality_prompt(cls, v: str) -> str:
        """Validate personality prompt."""
        v = v.strip()
        # Check for basic coherence - must have some words
        if len(v.split()) < 5:
            raise ValueError("Personality prompt must be at least 5 words")
        return v


class AgentCreateResponse(BaseModel):
    """Response schema for agent creation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    personality_prompt: str | None
    traits: dict
    location_id: str | None
    mood: dict
    state: str
    creator_id: int | None
    created_at: float | None
    is_user_created: bool


class AgentQuotaResponse(BaseModel):
    """Response schema for user agent quota information."""

    max_agents: int
    agents_created: int
    remaining: int
    can_create: bool
    next_creation_available_at: float | None = None


class AgentPreviewRequest(BaseModel):
    """Request schema for agent preview."""

    name: str = Field(..., min_length=2, max_length=50)
    personality_prompt: str = Field(..., min_length=20, max_length=1000)
    traits: TraitsSchema = Field(default_factory=TraitsSchema)
    location_id: str | None = None


class AgentPreviewResponse(BaseModel):
    """Response schema for agent preview."""

    name: str
    personality_prompt: str
    traits: dict
    location_name: str | None
    trait_summary: str
    personality_archetype: str
    compatibility_notes: list[str]


# Trait presets for common archetypes

TRAIT_PRESETS: dict[str, dict] = {
    "scholar": {
        "name": "Scholar",
        "description": "Curious and perceptive, focused on learning",
        "traits": {
            "curiosity": 9, "empathy": 5, "ambition": 6, "discretion": 7,
            "energy": 5, "courage": 4, "charm": 4, "perception": 8
        }
    },
    "merchant": {
        "name": "Merchant",
        "description": "Charming and ambitious, skilled at negotiation",
        "traits": {
            "curiosity": 5, "empathy": 5, "ambition": 8, "discretion": 6,
            "energy": 7, "courage": 5, "charm": 8, "perception": 7
        }
    },
    "guardian": {
        "name": "Guardian",
        "description": "Brave and empathetic, protective of others",
        "traits": {
            "curiosity": 4, "empathy": 8, "ambition": 4, "discretion": 6,
            "energy": 7, "courage": 9, "charm": 5, "perception": 6
        }
    },
    "trickster": {
        "name": "Trickster",
        "description": "Clever and charming, loves mischief",
        "traits": {
            "curiosity": 7, "empathy": 4, "ambition": 5, "discretion": 3,
            "energy": 8, "courage": 6, "charm": 8, "perception": 7
        }
    },
    "hermit": {
        "name": "Hermit",
        "description": "Wise and observant, prefers solitude",
        "traits": {
            "curiosity": 6, "empathy": 5, "ambition": 2, "discretion": 9,
            "energy": 3, "courage": 4, "charm": 3, "perception": 9
        }
    },
    "healer": {
        "name": "Healer",
        "description": "Compassionate and caring, dedicated to helping",
        "traits": {
            "curiosity": 5, "empathy": 9, "ambition": 3, "discretion": 7,
            "energy": 6, "courage": 5, "charm": 6, "perception": 7
        }
    },
    "leader": {
        "name": "Leader",
        "description": "Ambitious and charismatic, natural authority",
        "traits": {
            "curiosity": 5, "empathy": 6, "ambition": 9, "discretion": 5,
            "energy": 8, "courage": 8, "charm": 7, "perception": 6
        }
    },
    "artisan": {
        "name": "Artisan",
        "description": "Creative and dedicated, focused on craft",
        "traits": {
            "curiosity": 7, "empathy": 5, "ambition": 6, "discretion": 5,
            "energy": 6, "courage": 4, "charm": 5, "perception": 8
        }
    },
}


def get_trait_presets() -> dict[str, dict]:
    """Get all available trait presets."""
    return TRAIT_PRESETS


def get_preset_traits(preset_name: str) -> TraitsSchema | None:
    """Get traits for a specific preset."""
    preset = TRAIT_PRESETS.get(preset_name.lower())
    if preset:
        return TraitsSchema(**preset["traits"])
    return None


def generate_trait_summary(traits: TraitsSchema) -> str:
    """Generate a human-readable summary of traits."""
    summaries = []

    # Find dominant traits (>=7)
    if traits.curiosity >= 7:
        summaries.append("curious")
    if traits.empathy >= 7:
        summaries.append("empathetic")
    if traits.ambition >= 7:
        summaries.append("ambitious")
    if traits.discretion >= 7:
        summaries.append("discreet")
    if traits.energy >= 7:
        summaries.append("energetic")
    if traits.courage >= 7:
        summaries.append("courageous")
    if traits.charm >= 7:
        summaries.append("charming")
    if traits.perception >= 7:
        summaries.append("perceptive")

    # Find weak traits (<=3)
    weaknesses = []
    if traits.curiosity <= 3:
        weaknesses.append("incurious")
    if traits.empathy <= 3:
        weaknesses.append("cold")
    if traits.ambition <= 3:
        weaknesses.append("unambitious")
    if traits.discretion <= 3:
        weaknesses.append("indiscreet")
    if traits.energy <= 3:
        weaknesses.append("lethargic")
    if traits.courage <= 3:
        weaknesses.append("timid")
    if traits.charm <= 3:
        weaknesses.append("awkward")
    if traits.perception <= 3:
        weaknesses.append("oblivious")

    parts = []
    if summaries:
        parts.append(f"Strengths: {', '.join(summaries)}")
    if weaknesses:
        parts.append(f"Weaknesses: {', '.join(weaknesses)}")

    return ". ".join(parts) if parts else "Balanced personality"


def identify_archetype(traits: TraitsSchema) -> str:
    """Identify the closest personality archetype."""
    # Calculate similarity to each preset
    best_match = "Custom"
    best_score = 0

    trait_dict = traits.model_dump()

    for preset_name, preset_data in TRAIT_PRESETS.items():
        preset_traits = preset_data["traits"]
        # Calculate inverse of total difference
        diff = sum(abs(trait_dict[k] - preset_traits[k]) for k in trait_dict)
        score = 80 - diff  # Max possible difference is 72 (8 traits * 9)
        if score > best_score:
            best_score = score
            best_match = preset_data["name"]

    # Only return preset name if reasonably close
    if best_score >= 50:
        return best_match
    return "Unique"
