"""CLI commands implementation."""

import os
from pathlib import Path

from ..config.manager import load_sessions, save_sessions
from ..manager.observer import generate_report, run_manager
from ..session.manager import create_session as create_session_entry
from ..tmux.wrapper import (
    capture_pane,
    create_session as create_tmux_session,
    list_sessions,
)


def start_command(command: str | None = None, session_name: str | None = None) -> str:
    """Create new agent session.

    Args:
        command: Command to run in session (optional)
        session_name: Custom name for the session (optional)

    Returns:
        Session name
    """
    sessions = load_sessions()

    # Create session entry
    agent_name, session_entry = create_session_entry(command, sessions, session_name)

    # Create tmux session
    cwd = str(Path.cwd())
    success = create_tmux_session(agent_name, command, cwd)

    if not success:
        raise RuntimeError(f"Failed to create tmux session: {agent_name}")

    # Save to registry
    sessions[agent_name] = session_entry
    save_sessions(sessions)

    return agent_name


def list_command() -> list[str]:
    """List all active sessions.

    Returns:
        List of session names
    """
    return list_sessions()


def dump_command() -> dict[str, str]:
    """Display all session outputs.

    Returns:
        Dictionary of session_name -> output
    """
    sessions = list_sessions()
    outputs = {}

    for session_name in sessions:
        outputs[session_name] = capture_pane(session_name, lines=100)

    return outputs


def manager_command() -> list[dict]:
    """Run manager to check all sessions.

    Returns:
        List of session reports as dictionaries
    """
    sessions = load_sessions()
    updated_sessions = run_manager(sessions)
    save_sessions(updated_sessions)

    # Generate fresh reports for display
    reports = generate_report(sessions)
    return [report.model_dump() for report in reports]
