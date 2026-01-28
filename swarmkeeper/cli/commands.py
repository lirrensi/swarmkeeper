"""CLI commands implementation."""

import os
from pathlib import Path

from ..config.manager import load_sessions, save_sessions
from ..manager.loop import run_loop
from ..manager.observer import generate_report, run_manager
from ..session.manager import create_session as create_session_entry
from ..tmux.wrapper import (
    capture_pane,
    create_session as create_tmux_session,
    kill_session,
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


def stop_command(session_name: str) -> str:
    """Stop a tmux session (mirror of tmux kill-session).

    Args:
        session_name: Name of the session to stop

    Returns:
        Confirmation message
    """
    sessions = load_sessions()

    # Check if session exists in registry
    if session_name not in sessions:
        raise ValueError(
            f"Session '{session_name}' not found in registry. Use 'swarmkeeper list' to see active sessions."
        )

    # Kill tmux session
    if not kill_session(session_name):
        raise RuntimeError(f"Failed to kill tmux session: {session_name}")

    # Remove from registry
    del sessions[session_name]
    save_sessions(sessions)

    return f"Stopped session '{session_name}'"


def list_command() -> str:
    """List all active sessions with status and last log.

    Returns:
        Formatted string with session information
    """
    sessions = list_sessions()

    if not sessions:
        return "No active sessions"

    # Build formatted output
    output = "Active Sessions:\n"
    output += "=" * 60 + "\n"

    for session in sessions:
        name = session["name"]
        status = session["status"]
        log = session["log"]

        # Truncate log if too long
        if len(log) > 100:
            log = log[:97] + "..."

        # Format status indicator
        status_color = "[OK]" if status == "unknown" else "[?]"
        output += f"{name}: {status_color} {status}\n"
        output += f"  {log}\n"
        output += "-" * 60 + "\n"

    return output


def dump_command() -> dict[str, str]:
    """Display all session outputs.

    Returns:
        Dictionary of session_name -> output
    """
    sessions = list_sessions()
    outputs = {}

    for session in sessions:
        session_name = session["name"]
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


def manager_loop_command(interval: int | None = None, confirm: bool = False) -> dict:
    """Run manager loop with configurable interval.

    Repeatedly checks all sessions and stops when any session becomes stopped.
    Provides configurable timing and false positive prevention.

    Args:
        interval: Check interval in seconds. Default is 180 seconds (3 minutes).
        confirm: If True, requires 2 consecutive stopped checks per session before stopping
            to reduce false positives. Default is False.

    Returns:
        Updated sessions registry with new check entries.

    Behavior:
        - Loads sessions registry
        - Calls run_loop() with configured parameters
        - Displays user-friendly output
        - Saves registry after completion
        - Non-blocking - loop runs in foreground

    Example:
        >>> # Fast mode (default) - stops immediately on first stopped session
        >>> manager_loop_command()
        >>> # Check every minute
        >>> manager_loop_command(interval=60)
        >>> # Conservative mode - requires 2 consecutive checks
        >>> manager_loop_command(confirm=True)

    Raises:
        KeyboardInterrupt: If user interrupts with Ctrl+C
        Exception: If manager encounters errors during checks
    """
    # Load sessions registry
    sessions = load_sessions()

    # Display configuration
    print(f"\nRunning manager loop")
    print(f"  Interval: {interval or 180} seconds")
    print(f"  Confirmation mode: {'enabled' if confirm else 'disabled'}")
    print(f"  Sessions to monitor: {len(sessions)}")
    print("\nPress Ctrl+C to stop\n")

    # Run loop with configured parameters
    updated_sessions = run_loop(
        sessions, interval_seconds=interval or 180, require_confirmation=confirm
    )

    # Save registry
    save_sessions(updated_sessions)

    print(f"\nRegistry saved. {len(updated_sessions)} sessions tracked.")

    return updated_sessions
