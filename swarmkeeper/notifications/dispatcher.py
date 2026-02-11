"""Notification dispatcher - routes notifications to appropriate handler."""

import sys
from typing import Optional

from .core import NotificationPayload
from .handlers import notify_custom_handler, notify_os_default


def send_notification(
    payload: NotificationPayload,
    handler_command: Optional[str] = None,
) -> bool:
    """Send notification using specified or default handler.

    Args:
        payload: Notification payload with stats and events
        handler_command: Custom handler command path, or None for OS default,
                        or empty string to disable notifications

    Returns:
        True if notification was sent successfully

    Behavior:
        - If handler_command is None: Use OS default notification (plyer)
        - If handler_command is "": Disable notifications (return True silently)
        - If handler_command is provided: Execute custom handler with JSON via stdin
    """
    # Disabled notifications
    if handler_command == "":
        return True

    # Custom handler
    if handler_command is not None:
        return notify_custom_handler(handler_command, payload)

    # Default OS notification
    return notify_os_default(payload)
