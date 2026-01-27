"""Session management module."""

from .naming import generate_agent_name, ANIMALS
from .manager import create_session, add_check, is_session_alive

__all__ = [
    "generate_agent_name",
    "ANIMALS",
    "create_session",
    "add_check",
    "is_session_alive",
]
