"""Session management operations."""

import re
from datetime import datetime
from typing import Optional

from ..tmux.wrapper import session_exists


def validate_session_name(name: str) -> tuple[bool, str]:
    """Validate a custom session name.

    Args:
        name: Proposed session name

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Session name cannot be empty"

    # Tmux session names cannot contain . or :
    if "." in name or ":" in name:
        return False, "Session name cannot contain '.' or ':'"

    # Check for valid characters (alphanumeric, hyphen, underscore)
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return (
            False,
            "Session name can only contain letters, numbers, hyphens, and underscores",
        )

    return True, ""


def create_session(
    command: Optional[str],
    sessions_registry: dict,
    custom_name: Optional[str] = None,
) -> tuple[str, dict]:
    """Create new session entry with generated or custom name.

    Args:
        command: Command to run in session (optional)
        sessions_registry: Current sessions registry
        custom_name: Custom name for the session (optional)

    Returns:
        Tuple of (agent_name, session_entry)

    Raises:
        ValueError: If custom name is invalid or already exists
    """
    from .naming import generate_agent_name

    if custom_name:
        # Validate custom name
        is_valid, error_msg = validate_session_name(custom_name)
        if not is_valid:
            raise ValueError(f"Invalid session name: {error_msg}")

        # Check if name already exists in registry
        if custom_name in sessions_registry:
            raise ValueError(f"Session name '{custom_name}' already exists in registry")

        # Check if name already exists in tmux
        if session_exists(custom_name):
            raise ValueError(f"Session name '{custom_name}' already exists in tmux")

        agent_name = custom_name
    else:
        # Generate animal-based name
        existing_names = list(sessions_registry.keys())
        agent_name = generate_agent_name(existing_names)

    session_entry = {
        "created": datetime.now().isoformat(),
        "command": command if command else "",
        "checks": [],
    }

    return agent_name, session_entry


def add_check(session: dict, status: str, log: str) -> dict:
    """Append a check entry to session.

    Args:
        session: Session entry dict
        status: Status string ("working" or "stopped")
        log: Brief description of what agent was doing

    Returns:
        Updated session dict
    """
    check_entry = {"time": datetime.now().isoformat(), "status": status, "log": log}

    session["checks"].append(check_entry)
    return session


def is_session_alive(session_name: str) -> bool:
    """Check if tmux session is still active.

    Args:
        session_name: Name of the tmux session

    Returns:
        True if session exists and is active
    """
    return session_exists(session_name)
