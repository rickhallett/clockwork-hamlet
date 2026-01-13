"""Memory significance scoring."""


def calculate_significance(
    event_type: str,
    involves_self: bool = True,
    involves_friend: bool = False,
    involves_rival: bool = False,
    is_first_time: bool = False,
    emotional_impact: int = 0,
) -> int:
    """Calculate significance score for a memory (1-10).

    Args:
        event_type: Type of event (dialogue, action, discovery, etc.)
        involves_self: Whether the agent was directly involved
        involves_friend: Whether a friend was involved
        involves_rival: Whether a rival was involved
        is_first_time: Whether this is the first occurrence
        emotional_impact: Additional emotional weight (-3 to +3)

    Returns:
        Significance score 1-10
    """
    # Base significance by event type
    base_scores = {
        "dialogue": 3,
        "greeting": 2,
        "movement": 1,
        "action": 4,
        "discovery": 6,
        "relationship": 5,
        "conflict": 7,
        "secret": 8,
        "betrayal": 9,
        "romance": 7,
        "death": 10,
        "gift": 4,
        "help": 4,
        "insult": 6,
        "gossip": 5,
    }

    score = base_scores.get(event_type, 3)

    # Modifiers
    if involves_self:
        score += 1
    if involves_friend:
        score += 2
    if involves_rival:
        score += 2
    if is_first_time:
        score += 2

    # Emotional impact
    score += emotional_impact

    # Clamp to 1-10
    return max(1, min(10, score))


def decay_significance(current: int, hours_passed: int) -> int:
    """Decay significance over time.

    Memories become less significant as time passes,
    unless they were very significant to begin with.

    Args:
        current: Current significance score
        hours_passed: Hours since the memory was created

    Returns:
        New significance score (may be unchanged for high-significance memories)
    """
    # Very significant memories (8+) don't decay
    if current >= 8:
        return current

    # Calculate decay (1 point per 24 hours for moderate memories)
    days_passed = hours_passed // 24
    decay = days_passed // 2  # Lose 1 point every 2 days

    # Moderately significant memories (5-7) decay slower
    if current >= 5:
        decay = decay // 2

    return max(1, current - decay)
