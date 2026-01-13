"""Memory system for agent knowledge and experience."""

from hamlet.memory.compression import compress_memories, end_of_day_compression
from hamlet.memory.context import build_memory_context
from hamlet.memory.manager import (
    MemoryManager,
    add_memory,
    get_longterm_memories,
    get_recent_memories,
    get_working_memories,
)
from hamlet.memory.significance import calculate_significance
from hamlet.memory.types import MemoryType

__all__ = [
    # Types
    "MemoryType",
    # Manager
    "MemoryManager",
    "add_memory",
    "get_working_memories",
    "get_recent_memories",
    "get_longterm_memories",
    # Compression
    "compress_memories",
    "end_of_day_compression",
    # Context
    "build_memory_context",
    # Significance
    "calculate_significance",
]
