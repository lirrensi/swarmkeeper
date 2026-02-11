"""Core notification types and payload builder."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SessionInfo:
    """Information about a single session."""

    name: str
    status: str
    is_alive: bool
    last_log: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "is_alive": self.is_alive,
            "last_log": self.last_log,
        }


@dataclass
class EventInfo:
    """Information about a single event."""

    event_type: str
    agent_name: str
    agent_status: str
    agent_last_log: str
    message: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "agent": {
                "name": self.agent_name,
                "status": self.agent_status,
                "last_log": self.agent_last_log,
            },
            "message": self.message,
        }


@dataclass
class NotificationPayload:
    """Complete notification payload with stats and events."""

    stats: dict
    events: List[dict]
    meta: dict

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stats": self.stats,
            "events": self.events,
            "meta": self.meta,
        }


def create_notification_payload(
    sessions_registry: Dict[str, dict],
    stopped_sessions: List[str],
    loop_iteration: int,
    check_duration_ms: Optional[int] = None,
) -> NotificationPayload:
    """Create a notification payload from session data.

    Args:
        sessions_registry: Current sessions registry
        stopped_sessions: List of session names that stopped in this check
        loop_iteration: Current loop iteration number
        check_duration_ms: Duration of the check in milliseconds (optional)

    Returns:
        NotificationPayload with aggregated stats and events
    """
    # Build session list with current status
    sessions = []
    for name, data in sessions_registry.items():
        sessions.append(
            SessionInfo(
                name=name,
                status=data.get("last_status", "unknown"),
                is_alive=data.get("is_alive", True),
                last_log=data.get("last_log", ""),
            )
        )

    # Calculate stats
    total = len(sessions)
    active = sum(1 for s in sessions if s.is_alive)
    stopped = total - active

    # Build events list for stopped sessions
    events = []
    for session_name in stopped_sessions:
        if session_name in sessions_registry:
            session_data = sessions_registry[session_name]
            last_log = session_data.get("last_log", "No log available")
            last_status = session_data.get("last_status", "unknown")

            # Determine event type based on status/log
            event_type = _determine_event_type(last_status, last_log)

            events.append(
                EventInfo(
                    event_type=event_type,
                    agent_name=session_name,
                    agent_status=last_status,
                    agent_last_log=last_log,
                    message=_create_event_message(session_name, event_type, last_log),
                )
            )

    # Build payload
    return NotificationPayload(
        stats={
            "total_sessions": total,
            "active_sessions": active,
            "stopped_sessions": stopped,
            "sessions": [s.to_dict() for s in sessions],
        },
        events=[e.to_dict() for e in events],
        meta={
            "timestamp": datetime.now().isoformat(),
            "loop_iteration": loop_iteration,
            "check_duration_ms": check_duration_ms,
        },
    )


def _determine_event_type(status: str, last_log: str) -> str:
    """Determine event type from status and log content."""
    log_lower = last_log.lower()

    if "error" in log_lower or "exception" in log_lower or "failed" in log_lower:
        return "error"
    elif "complete" in log_lower or "finished" in log_lower or "done" in log_lower:
        return "completed"
    elif "stuck" in log_lower or "frozen" in log_lower:
        return "stuck"
    elif "idle" in log_lower or "waiting" in log_lower:
        return "idle"
    else:
        return "stopped"


def _create_event_message(session_name: str, event_type: str, last_log: str) -> str:
    """Create a human-readable event message."""
    messages = {
        "error": f"Session '{session_name}' stopped with error",
        "completed": f"Session '{session_name}' completed successfully",
        "stuck": f"Session '{session_name}' appears to be stuck",
        "idle": f"Session '{session_name}' went idle",
        "stopped": f"Session '{session_name}' has stopped",
    }
    return messages.get(event_type, messages["stopped"])
