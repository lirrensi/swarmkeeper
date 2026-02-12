"""Pattern-based monitoring module for SwarmKeeper.

Provides simple text-based pattern matching as an alternative to LLM-based monitoring.
Supports multiple patterns, fuzzy matching, and auto-type intervention.
"""

from .observer import check_patterns, generate_pattern_report, PatternResult
from .loop import run_pattern_loop

__all__ = [
    "check_patterns",
    "generate_pattern_report",
    "PatternResult",
    "run_pattern_loop",
]
