"""Memory type definitions."""

from enum import Enum


class MemoryType(str, Enum):
    """Types of memories in the memory hierarchy."""

    WORKING = "working"  # Recent, uncompressed memories (last 5-10 interactions)
    RECENT = "recent"  # Daily summaries, compressed from working memories
    LONGTERM = "longterm"  # Compressed facts and important events


# Configuration for memory limits
WORKING_MEMORY_LIMIT = 10  # Max working memories before compression
RECENT_MEMORY_LIMIT = 7  # Keep last 7 days of summaries
LONGTERM_MEMORY_LIMIT = 50  # Max long-term facts to keep

# Significance thresholds
SIGNIFICANCE_THRESHOLD_FOR_LONGTERM = 6  # Min significance to become long-term
SIGNIFICANCE_THRESHOLD_FOR_SUMMARY = 4  # Min significance to include in daily summary
