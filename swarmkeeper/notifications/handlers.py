"""Notification handlers for different output channels."""

import json
import subprocess
import sys
from typing import Optional

from .core import NotificationPayload


def notify_os_default(payload: NotificationPayload) -> bool:
    """Send OS-native notification with aggregated message.

    Uses plyer for cross-platform notifications. Falls back to
    terminal bell if plyer is not available.

    Args:
        payload: Notification payload with stats and events

    Returns:
        True if notification was sent successfully
    """
    try:
        from plyer import notification

        # Build aggregated message
        title, message = _format_notification(payload)

        # Send notification
        notification.notify(
            title=title,
            message=message,
            app_name="SwarmKeeper",
            timeout=10,
        )
        return True

    except ImportError:
        # plyer not installed, use fallback
        return _notify_fallback(payload)

    except Exception as e:
        print(f"Warning: OS notification failed: {e}", file=sys.stderr)
        return False


def _format_notification(payload: NotificationPayload) -> tuple:
    """Format payload into title and message for display.

    Args:
        payload: Notification payload

    Returns:
        Tuple of (title, message)
    """
    stats = payload.stats
    events = payload.events

    # Count events by type
    event_counts = {}
    for event in events:
        etype = event["event_type"]
        event_counts[etype] = event_counts.get(etype, 0) + 1

    # Build title
    total_events = len(events)
    if total_events == 1:
        event = events[0]
        title = f"🐝 {event['event_type'].title()}: {event['agent']['name']}"
    else:
        # Multiple events - summarize
        parts = []
        for etype, count in sorted(event_counts.items()):
            parts.append(f"{count} {etype}")
        title = f"🐝 SwarmKeeper: {', '.join(parts)}"

    # Build message
    lines = []

    # Add event details (first 3)
    for event in events[:3]:
        agent = event["agent"]
        lines.append(f"• {agent['name']}: {agent['last_log'][:50]}")

    # If more events, add ellipsis
    if len(events) > 3:
        lines.append(f"• ... and {len(events) - 3} more")

    # Add summary
    lines.append("")
    lines.append(f"{stats['active_sessions']} of {stats['total_sessions']} sessions active")

    return title, "\n".join(lines)


def _notify_fallback(payload: NotificationPayload) -> bool:
    """Fallback notification using terminal bell and print.

    Args:
        payload: Notification payload

    Returns:
        Always True (never fails)
    """
    title, message = _format_notification(payload)

    print(f"\n{'=' * 50}")
    print(f"🔔 NOTIFICATION: {title}")
    print(f"{'=' * 50}")
    print(message)
    print(f"{'=' * 50}\n")

    # Terminal bell
    print("\a", end="")
    return True


def notify_custom_handler(handler_command: str, payload: NotificationPayload) -> bool:
    """Send notification to custom handler via stdin.

    Args:
        handler_command: Command to execute (can include arguments)
        payload: Notification payload to send as JSON

    Returns:
        True if handler executed successfully
    """
    try:
        # Convert payload to JSON
        json_data = json.dumps(payload.to_dict(), indent=2)

        # Execute handler with JSON via stdin
        result = subprocess.run(
            handler_command,
            shell=True,
            input=json_data,
            text=True,
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(
                f"Warning: Custom handler failed with code {result.returncode}",
                file=sys.stderr,
            )
            if result.stderr:
                print(f"Handler stderr: {result.stderr}", file=sys.stderr)
            return False

        return True

    except subprocess.TimeoutExpired:
        print("Warning: Custom handler timed out after 30s", file=sys.stderr)
        return False

    except Exception as e:
        print(f"Warning: Failed to run custom handler: {e}", file=sys.stderr)
        return False
