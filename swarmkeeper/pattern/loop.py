"""Pattern loop control for continuous pattern-based monitoring.

Provides continuous monitoring with auto-type intervention when patterns are detected.
"""

from time import sleep
from typing import Dict, List, Optional

from ..config.manager import save_sessions
from ..notifications import create_notification_payload, send_notification
from ..tmux.wrapper import send_keys
from .observer import check_patterns, generate_pattern_report, PatternResult


def run_pattern_loop(
    sessions_registry: Dict[str, dict],
    patterns: List[str],
    use_regex: bool = False,
    use_fuzzy: bool = False,
    fuzzy_threshold: float = 80.0,
    lines: int = 100,
    interval_seconds: int = 60,
    auto_type: Optional[str] = None,
    auto_type_max: int = 2,
    require_confirmation: bool = False,
    notify_handler: Optional[str] = None,
) -> Dict[str, dict]:
    """Run continuous pattern monitoring loop.

    Continuously checks all sessions for pattern matches. When a pattern is detected,
    optionally sends keystrokes to the session (auto-type). Stops when auto-type
    max is reached for any session.

    Args:
        sessions_registry: Current sessions registry (session_name -> session_data)
        patterns: List of patterns to search for (OR logic)
        use_regex: If True, treat patterns as regex
        use_fuzzy: If True, use fuzzy matching
        fuzzy_threshold: Minimum similarity for fuzzy match (0-100)
        lines: Number of lines to capture from each session
        interval_seconds: Time between checks in seconds
        auto_type: Keys to send when pattern detected (None = no auto-type)
        auto_type_max: Max auto-type interventions per session before stopping
        require_confirmation: If True, requires 2 consecutive detections before action
        notify_handler: Notification handler path, empty string to disable, or None for OS default

    Returns:
        Updated sessions registry

    Behavior:
        - Runs continuously until stopped or auto-type-max reached
        - Tracks auto-type count per session
        - Saves registry after each check
        - Gracefully handles Ctrl+C
        - Reports which pattern matched for each session

    Example:
        >>> registry = load_sessions()
        >>> run_pattern_loop(
        ...     registry,
        ...     patterns=["error", "failed"],
        ...     interval_seconds=30,
        ...     auto_type="y\n",
        ...     auto_type_max=3,
        ... )
    """
    iteration = 0
    auto_type_counts: Dict[str, int] = {}
    confirmation_pending: Dict[str, PatternResult] = {}

    try:
        while True:
            iteration += 1
            print(f"\n[Pattern check #{iteration}] Checking for patterns: {patterns}")

            # Generate pattern report for all sessions
            results = generate_pattern_report(
                sessions_registry=sessions_registry,
                patterns=patterns,
                use_regex=use_regex,
                use_fuzzy=use_fuzzy,
                fuzzy_threshold=fuzzy_threshold,
                lines=lines,
            )

            # Process results
            matched_sessions = []
            dead_sessions = []

            for result in results:
                session_name = result.session_name

                if not result.is_alive:
                    dead_sessions.append(session_name)
                    print(f"  [!] {session_name}: Session is dead")
                    continue

                if result.matched:
                    matched_sessions.append(session_name)
                    pattern_display = result.matched_pattern or "unknown"
                    print(f"  [MATCH] {session_name}: '{pattern_display}'")
                    matched_text = result.matched_text or ""
                    print(f"    -> {matched_text[:80]}...")

                    # Handle confirmation mode
                    if require_confirmation:
                        if session_name in confirmation_pending:
                            # Second consecutive match - proceed with action
                            print(f"    -> Confirmed (2nd consecutive detection)")
                            del confirmation_pending[session_name]
                        else:
                            # First match - wait for confirmation
                            print(
                                f"    -> Waiting for confirmation (check again in {interval_seconds}s)"
                            )
                            confirmation_pending[session_name] = result
                            continue

                    # Handle auto-type
                    if auto_type is not None:
                        current_count = auto_type_counts.get(session_name, 0)

                        if current_count >= auto_type_max:
                            print(
                                f"    -> Auto-type max ({auto_type_max}) reached for {session_name}"
                            )
                            print(f"\nStopping loop: auto-type-max reached")
                            return sessions_registry

                        # Send keys to session
                        print(f"    -> Auto-typing: {repr(auto_type)}")
                        success = send_keys(session_name, auto_type)

                        if success:
                            auto_type_counts[session_name] = current_count + 1
                            print(f"    -> Auto-type count: {current_count + 1}/{auto_type_max}")
                        else:
                            print(f"    -> [ERROR] Failed to send keys to {session_name}")

            # Remove dead sessions from registry
            for session_name in dead_sessions:
                if session_name in sessions_registry:
                    print(f"  Removing dead session from registry: {session_name}")
                    del sessions_registry[session_name]
                if session_name in confirmation_pending:
                    del confirmation_pending[session_name]

            # Save registry after each iteration
            save_sessions(sessions_registry)

            # Send notification if patterns matched (and auto-type is None, meaning we're in report mode)
            if matched_sessions and auto_type is None and notify_handler != "":
                try:
                    payload = create_notification_payload(
                        sessions_registry=sessions_registry,
                        stopped_sessions=matched_sessions,  # Treat matched as "stopped" for notification
                        loop_iteration=iteration,
                    )
                    send_notification(payload, handler_command=notify_handler)
                except Exception as e:
                    print(f"  [Notification error: {e}]")

            # Check if we should continue
            if matched_sessions and auto_type is None:
                # No auto-type, just reporting - exit after first detection
                print(f"\nPattern(s) detected in: {', '.join(matched_sessions)}")
                print("Stopping loop (no auto-type configured)")
                return sessions_registry

            if not sessions_registry:
                print("\nNo sessions remaining. Stopping loop.")
                return sessions_registry

            # Wait before next iteration
            print(f"\nWaiting {interval_seconds} seconds before next check...")
            sleep(interval_seconds)

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
