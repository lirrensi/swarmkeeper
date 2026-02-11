"""Manager loop control for continuous session monitoring."""

import os
from time import sleep
from datetime import datetime
from typing import Dict, Optional

from ..config.manager import load_sessions, save_sessions
from ..notifications import create_notification_payload, send_notification
from .observer import run_manager


def run_loop(
    sessions_registry: Dict[str, dict],
    interval_seconds: int = 180,
    require_confirmation: bool = False,
    notify_handler: Optional[str] = None,
) -> Dict[str, dict]:
    """Run continuous monitoring loop.

    Repeatedly checks all sessions using the manager and stops when any session
    becomes stopped. Provides configurable timing and false positive prevention.

    Args:
        sessions_registry: Current sessions registry (session_name -> session_data).
            Loaded via load_sessions() before calling.
        interval_seconds: Time between checks in seconds. Default is 180 seconds (3 minutes).
        require_confirmation: If True, requires 2 consecutive stopped checks per session
            before stopping to reduce false positives. Default is False.
        notify_handler: Notification handler path, empty string to disable, or None for OS default.

    Returns:
        Updated sessions registry with new check entries.

    Behavior:
        - Runs manager repeatedly with configurable interval
        - Stops when ANY session is stopped (alive=False)
        - If require_confirmation=True, requires 2 consecutive stopped checks per session
        - Saves registry after each check
        - Non-blocking - reports and exits
        - Gracefully handles Ctrl+C
        - Sends notifications when sessions stop (if enabled)

    Example:
        >>> # Fast mode (default) - stops immediately on first stopped session
        >>> registry = load_sessions()
        >>> run_loop(registry, interval_seconds=60)  # Check every minute

        >>> # Conservative mode - requires 2 consecutive checks
        >>> registry = load_sessions()
        >>> run_loop(registry, interval_seconds=60, require_confirmation=True)

    Notes:
        - Loop runs in foreground (not daemon)
        - User can interrupt with Ctrl+C
        - No token waste from checking idle sessions
        - Configurable balance between speed and efficiency
        - False positive prevention via confirmation mode
        - Notifications sent when sessions stop (if handler configured)

    Raises:
        KeyboardInterrupt: If user interrupts with Ctrl+C
        Exception: If manager encounters errors during checks
    """
    iteration = 0

    try:
        while True:
            iteration += 1
            print(f"\n[Loop check #{iteration}] Checking sessions...")

            # Run manager to check all sessions
            updated_registry = run_manager(sessions_registry)

            # Check for stopped sessions
            stopped_sessions = []
            for session_name, session_data in updated_registry.items():
                if not session_data.get("is_alive", True):
                    stopped_sessions.append(session_name)

            # Display results
            if stopped_sessions:
                print(f"\nDetected stopped session(s): {', '.join(stopped_sessions)}")
                for session_name in stopped_sessions:
                    session = updated_registry[session_name]
                    print(
                        f"  {session_name}: {session.get('last_status', 'unknown')} - {session.get('last_log', 'No log')}"
                    )

                # Send notification (if not disabled)
                if notify_handler != "":
                    try:
                        payload = create_notification_payload(
                            sessions_registry=updated_registry,
                            stopped_sessions=stopped_sessions,
                            loop_iteration=iteration,
                        )
                        send_notification(payload, handler_command=notify_handler)
                    except Exception as e:
                        print(f"  [Notification error: {e}]")

                # Exit condition
                if not require_confirmation:
                    print("\nStopping loop (fast mode).")
                    break
                else:
                    print("\nChecking again in {} seconds to confirm...".format(interval_seconds))
                    sleep(interval_seconds)
                    continue
            else:
                print("All sessions are active. Continuing check...")

            # Wait before next iteration
            if iteration > 1:  # Sleep after first iteration completes
                sleep(interval_seconds)

            # Update sessions registry
            sessions_registry = updated_registry

        # Always return registry
        return sessions_registry

    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        print("Saving registry before exit...")
        save_sessions(sessions_registry)
        print("Goodbye!")
        raise
    except Exception as e:
        print(f"\n\n[Error during loop execution: {e}]")
        print("Saving registry before exit...")
        save_sessions(sessions_registry)
        raise
    finally:
        # Ensure registry is always saved before exit
        save_sessions(sessions_registry)

    # This line is never reached, but needed for type checker
    return sessions_registry
