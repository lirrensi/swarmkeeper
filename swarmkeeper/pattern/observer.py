"""Pattern observer module for text-based session monitoring.

Provides pattern matching with support for:
- Multiple patterns (OR logic)
- Literal substring matching
- Regex pattern matching
- Fuzzy matching (whitespace normalization, case insensitive)
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from ..tmux.wrapper import capture_pane, session_exists


@dataclass
class PatternResult:
    """Result of pattern check for a single session."""

    session_name: str
    matched: bool
    matched_pattern: Optional[str] = None
    matched_text: Optional[str] = None
    line_count: int = 0
    is_alive: bool = True


def _normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching.

    - Converts to lowercase
    - Collapses multiple whitespace to single space
    - Strips leading/trailing whitespace
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two strings (0-100).

    Uses a simple character-based approach suitable for short patterns.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize both texts
    t1 = _normalize_text(text1)
    t2 = _normalize_text(text2)

    if t1 == t2:
        return 100.0

    # Simple Levenshtein-inspired distance for short strings
    len1, len2 = len(t1), len(t2)
    max_len = max(len1, len2)

    if max_len == 0:
        return 100.0

    # Count matching characters
    matches = 0
    min_len = min(len1, len2)
    for i in range(min_len):
        if t1[i] == t2[i]:
            matches += 1

    # Calculate similarity percentage
    similarity = (matches / max_len) * 100

    # Bonus for substring match
    if t1 in t2 or t2 in t1:
        similarity = max(similarity, 80.0)

    return similarity


def _check_fuzzy_match(
    text: str, pattern: str, threshold: float = 80.0
) -> tuple[bool, Optional[str]]:
    """Check if pattern fuzzy matches anywhere in text.

    Args:
        text: Text to search in
        pattern: Pattern to search for
        threshold: Minimum similarity threshold (0-100)

    Returns:
        Tuple of (matched, matched_text)
    """
    normalized_text = _normalize_text(text)
    normalized_pattern = _normalize_text(pattern)

    # Direct substring match after normalization
    if normalized_pattern in normalized_text:
        # Find the actual matched text in original
        # Map back to approximate position in original
        words = normalized_pattern.split()
        if words:
            # Try to find the words in original text
            for line in text.split("\n"):
                normalized_line = _normalize_text(line)
                if all(word in normalized_line for word in words):
                    return True, line.strip()
        return True, text.strip()[:100]  # Return first 100 chars if can't locate exactly

    # Check similarity for the whole text
    similarity = _calculate_similarity(normalized_text, normalized_pattern)
    if similarity >= threshold:
        return True, text.strip()[:100]

    # Check line by line for better precision
    for line in text.split("\n"):
        normalized_line = _normalize_text(line)
        if normalized_pattern in normalized_line:
            return True, line.strip()

        # Check word-level matching for better fuzzy support
        pattern_words = normalized_pattern.split()
        line_words = normalized_line.split()
        if pattern_words and line_words:
            # Check if all pattern words appear in line (in any order)
            all_words_found = all(
                any(_calculate_similarity(pw, lw) >= threshold for lw in line_words)
                or any(pw in lw for lw in line_words)
                for pw in pattern_words
            )
            if all_words_found:
                return True, line.strip()

        line_similarity = _calculate_similarity(normalized_line, normalized_pattern)
        if line_similarity >= threshold:
            return True, line.strip()

    return False, None


def check_patterns(
    session_name: str,
    patterns: List[str],
    use_regex: bool = False,
    use_fuzzy: bool = False,
    fuzzy_threshold: float = 80.0,
    lines: int = 100,
) -> PatternResult:
    """Check if any pattern exists in session output.

    Args:
        session_name: Name of the tmux session
        patterns: List of patterns to search for (OR logic - any match triggers)
        use_regex: If True, treat patterns as regex
        use_fuzzy: If True, use fuzzy matching
        fuzzy_threshold: Minimum similarity for fuzzy match (0-100)
        lines: Number of lines to capture from session

    Returns:
        PatternResult with match information
    """
    # Check if session exists
    is_alive = session_exists(session_name)

    if not is_alive:
        return PatternResult(
            session_name=session_name,
            matched=False,
            is_alive=False,
            line_count=0,
        )

    # Capture session output
    session_output = capture_pane(session_name, lines=lines)
    line_count = len([l for l in session_output.split("\n") if l.strip()])

    # Check each pattern
    for pattern in patterns:
        if use_regex:
            # Regex matching
            try:
                flags = re.IGNORECASE if use_fuzzy else 0
                match = re.search(pattern, session_output, flags)
                if match:
                    return PatternResult(
                        session_name=session_name,
                        matched=True,
                        matched_pattern=pattern,
                        matched_text=match.group(0),
                        line_count=line_count,
                        is_alive=True,
                    )
            except re.error:
                # Invalid regex, skip this pattern
                continue
        elif use_fuzzy:
            # Fuzzy matching
            matched, matched_text = _check_fuzzy_match(session_output, pattern, fuzzy_threshold)
            if matched:
                return PatternResult(
                    session_name=session_name,
                    matched=True,
                    matched_pattern=pattern,
                    matched_text=matched_text,
                    line_count=line_count,
                    is_alive=True,
                )
        else:
            # Literal substring matching
            if pattern in session_output:
                # Find the line containing the pattern
                for line in session_output.split("\n"):
                    if pattern in line:
                        return PatternResult(
                            session_name=session_name,
                            matched=True,
                            matched_pattern=pattern,
                            matched_text=line.strip(),
                            line_count=line_count,
                            is_alive=True,
                        )

    # No patterns matched
    return PatternResult(
        session_name=session_name,
        matched=False,
        line_count=line_count,
        is_alive=True,
    )


def generate_pattern_report(
    sessions_registry: dict,
    patterns: List[str],
    use_regex: bool = False,
    use_fuzzy: bool = False,
    fuzzy_threshold: float = 80.0,
    lines: int = 100,
) -> List[PatternResult]:
    """Generate pattern check report for all tracked sessions.

    Args:
        sessions_registry: Dictionary of session_name -> session_data
        patterns: List of patterns to search for
        use_regex: If True, treat patterns as regex
        use_fuzzy: If True, use fuzzy matching
        fuzzy_threshold: Minimum similarity for fuzzy match
        lines: Number of lines to capture from each session

    Returns:
        List of PatternResult for each session
    """
    results = []

    for session_name in sessions_registry.keys():
        result = check_patterns(
            session_name=session_name,
            patterns=patterns,
            use_regex=use_regex,
            use_fuzzy=use_fuzzy,
            fuzzy_threshold=fuzzy_threshold,
            lines=lines,
        )
        results.append(result)

    return results
