"""Tests for the notification module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from swarmkeeper.notifications import (
    NotificationPayload,
    create_notification_payload,
    send_notification,
)
from swarmkeeper.notifications.core import EventInfo, SessionInfo, _determine_event_type
from swarmkeeper.notifications.dispatcher import _route_notification
from swarmkeeper.notifications.handlers import _format_notification, notify_os_default


class TestSessionInfo:
    """Tests for SessionInfo dataclass."""

    def test_session_info_creation(self):
        """Test creating a SessionInfo object."""
        session = SessionInfo(
            name="test-session",
            status="running",
            is_alive=True,
            last_log="Processing task...",
        )
        assert session.name == "test-session"
        assert session.status == "running"
        assert session.is_alive is True
        assert session.last_log == "Processing task..."

    def test_session_info_to_dict(self):
        """Test converting SessionInfo to dictionary."""
        session = SessionInfo(
            name="test-session",
            status="stopped",
            is_alive=False,
            last_log="Task completed",
        )
        result = session.to_dict()
        assert result == {
            "name": "test-session",
            "status": "stopped",
            "is_alive": False,
            "last_log": "Task completed",
        }


class TestEventInfo:
    """Tests for EventInfo dataclass."""

    def test_event_info_creation(self):
        """Test creating an EventInfo object."""
        event = EventInfo(
            event_type="completed",
            agent_name="test-session",
            agent_status="stopped",
            agent_last_log="Task completed successfully",
            message="Session completed",
        )
        assert event.event_type == "completed"
        assert event.agent_name == "test-session"

    def test_event_info_to_dict(self):
        """Test converting EventInfo to dictionary."""
        event = EventInfo(
            event_type="error",
            agent_name="test-session",
            agent_status="stopped",
            agent_last_log="Error occurred",
            message="Session failed",
        )
        result = event.to_dict()
        assert result["event_type"] == "error"
        assert result["agent"]["name"] == "test-session"
        assert result["agent"]["status"] == "stopped"
        assert result["message"] == "Session failed"


class TestDetermineEventType:
    """Tests for event type detection."""

    def test_error_detection(self):
        """Test detecting error events."""
        assert _determine_event_type("stopped", "An error occurred") == "error"
        assert _determine_event_type("stopped", "Exception in thread") == "error"
        assert _determine_event_type("stopped", "Task failed") == "error"

    def test_completed_detection(self):
        """Test detecting completed events."""
        assert _determine_event_type("stopped", "Task completed") == "completed"
        assert _determine_event_type("stopped", "Processing finished") == "completed"
        assert _determine_event_type("stopped", "All done") == "completed"

    def test_stuck_detection(self):
        """Test detecting stuck events."""
        assert _determine_event_type("stopped", "Process appears stuck") == "stuck"
        assert _determine_event_type("stopped", "System frozen") == "stuck"

    def test_idle_detection(self):
        """Test detecting idle events."""
        assert _determine_event_type("stopped", "Session went idle") == "idle"
        assert _determine_event_type("stopped", "Waiting for input") == "idle"

    def test_default_stopped(self):
        """Test default stopped type."""
        assert _determine_event_type("stopped", "Some random log") == "stopped"


class TestCreateNotificationPayload:
    """Tests for payload creation."""

    def test_payload_structure(self):
        """Test that payload has correct structure."""
        registry = {
            "session1": {
                "is_alive": True,
                "last_status": "running",
                "last_log": "Processing...",
            },
            "session2": {
                "is_alive": False,
                "last_status": "stopped",
                "last_log": "Task completed",
            },
        }

        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["session2"],
            loop_iteration=5,
        )

        assert isinstance(payload, NotificationPayload)
        assert payload.stats["total_sessions"] == 2
        assert payload.stats["active_sessions"] == 1
        assert payload.stats["stopped_sessions"] == 1
        assert len(payload.stats["sessions"]) == 2
        assert len(payload.events) == 1
        assert payload.meta["loop_iteration"] == 5
        assert "timestamp" in payload.meta

    def test_event_type_in_payload(self):
        """Test that correct event type is included."""
        registry = {
            "session1": {
                "is_alive": False,
                "last_status": "stopped",
                "last_log": "Error: something went wrong",
            },
        }

        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["session1"],
            loop_iteration=1,
        )

        assert payload.events[0]["event_type"] == "error"
        assert "error" in payload.events[0]["message"].lower()

    def test_multiple_stopped_sessions(self):
        """Test payload with multiple stopped sessions."""
        registry = {
            "session1": {"is_alive": False, "last_status": "stopped", "last_log": "Done"},
            "session2": {"is_alive": False, "last_status": "stopped", "last_log": "Error"},
            "session3": {"is_alive": True, "last_status": "running", "last_log": "Working"},
        }

        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["session1", "session2"],
            loop_iteration=3,
        )

        assert payload.stats["total_sessions"] == 3
        assert payload.stats["stopped_sessions"] == 2
        assert len(payload.events) == 2

    def test_payload_to_dict(self):
        """Test converting payload to dictionary."""
        registry = {
            "session1": {"is_alive": False, "last_status": "stopped", "last_log": "Done"},
        }

        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["session1"],
            loop_iteration=1,
        )

        result = payload.to_dict()
        assert "stats" in result
        assert "events" in result
        assert "meta" in result
        assert isinstance(result["stats"], dict)
        assert isinstance(result["events"], list)
        assert isinstance(result["meta"], dict)


class TestSendNotification:
    """Tests for notification dispatching."""

    def create_test_payload(self):
        """Helper to create a test payload."""
        return NotificationPayload(
            stats={
                "total_sessions": 1,
                "active_sessions": 0,
                "stopped_sessions": 1,
                "sessions": [],
            },
            events=[
                {
                    "event_type": "completed",
                    "agent": {
                        "name": "test",
                        "status": "stopped",
                        "last_log": "Done",
                    },
                    "message": "Test completed",
                }
            ],
            meta={
                "timestamp": "2026-01-28T10:00:00Z",
                "loop_iteration": 1,
                "check_duration_ms": None,
            },
        )

    def test_disabled_mode(self):
        """Test that empty string disables notifications."""
        payload = self.create_test_payload()
        result = send_notification(payload, handler_command="")
        assert result is True

    def test_os_default_notification(self):
        """Test OS default notification (uses fallback)."""
        payload = self.create_test_payload()
        result = send_notification(payload, handler_command=None)
        assert result is True

    def test_custom_handler_success(self):
        """Test custom handler execution."""
        # Create a temporary script that writes to a file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                "import sys, json; "
                "data = json.load(sys.stdin); "
                "print('Received notification for', data['stats']['total_sessions'], 'sessions')"
            )
            script_path = f.name

        try:
            payload = self.create_test_payload()
            result = send_notification(payload, handler_command=f"python {script_path}")
            assert result is True
        finally:
            os.unlink(script_path)

    def test_custom_handler_failure(self):
        """Test custom handler failure handling."""
        payload = self.create_test_payload()
        # Use a command that will fail
        result = send_notification(payload, handler_command="false")
        assert result is False


class TestFormatNotification:
    """Tests for notification formatting."""

    def test_single_event_formatting(self):
        """Test formatting with single event."""
        payload = NotificationPayload(
            stats={
                "total_sessions": 2,
                "active_sessions": 1,
                "stopped_sessions": 1,
                "sessions": [],
            },
            events=[
                {
                    "event_type": "completed",
                    "agent": {"name": "session1", "status": "stopped", "last_log": "Task done"},
                    "message": "Session completed",
                }
            ],
            meta={},
        )

        title, message = _format_notification(payload)
        assert "completed" in title.lower()
        assert "session1" in title
        assert "session1" in message
        assert "Task done" in message

    def test_multiple_events_formatting(self):
        """Test formatting with multiple events."""
        payload = NotificationPayload(
            stats={
                "total_sessions": 3,
                "active_sessions": 1,
                "stopped_sessions": 2,
                "sessions": [],
            },
            events=[
                {
                    "event_type": "completed",
                    "agent": {"name": "session1", "status": "stopped", "last_log": "Done"},
                    "message": "Completed",
                },
                {
                    "event_type": "error",
                    "agent": {"name": "session2", "status": "stopped", "last_log": "Error"},
                    "message": "Error occurred",
                },
            ],
            meta={},
        )

        title, message = _format_notification(payload)
        assert "1 completed" in title or "1 error" in title
        assert "1 of 3 sessions active" in message

    def test_event_truncation(self):
        """Test that long logs are truncated."""
        long_log = "A" * 100
        payload = NotificationPayload(
            stats={
                "total_sessions": 1,
                "active_sessions": 0,
                "stopped_sessions": 1,
                "sessions": [],
            },
            events=[
                {
                    "event_type": "completed",
                    "agent": {"name": "session1", "status": "stopped", "last_log": long_log},
                    "message": "Done",
                }
            ],
            meta={},
        )

        title, message = _format_notification(payload)
        # Should be truncated to 50 chars
        assert len(message.split("\n")[0]) < 60


class TestRouteNotification:
    """Tests for notification routing."""

    def test_route_disabled(self):
        """Test routing when disabled."""
        payload = NotificationPayload(stats={}, events=[], meta={})
        result = _route_notification(payload, "")
        assert result is True

    def test_route_os_default(self):
        """Test routing to OS default."""
        payload = NotificationPayload(
            stats={
                "total_sessions": 1,
                "active_sessions": 0,
                "stopped_sessions": 1,
                "sessions": [],
            },
            events=[
                {
                    "event_type": "completed",
                    "agent": {"name": "test", "status": "stopped", "last_log": "Done"},
                    "message": "Done",
                }
            ],
            meta={},
        )
        result = _route_notification(payload, None)
        assert result is True


class TestIntegration:
    """Integration tests for the notification module."""

    def test_full_notification_flow(self):
        """Test complete flow from registry to notification."""
        # Setup
        registry = {
            "agent-1": {
                "is_alive": False,
                "last_status": "stopped",
                "last_log": "Task completed successfully",
            },
            "agent-2": {
                "is_alive": True,
                "last_status": "running",
                "last_log": "Processing...",
            },
        }

        # Create payload
        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["agent-1"],
            loop_iteration=42,
        )

        # Verify payload
        assert payload.stats["total_sessions"] == 2
        assert payload.stats["active_sessions"] == 1
        assert payload.stats["stopped_sessions"] == 1
        assert len(payload.events) == 1
        assert payload.events[0]["event_type"] == "completed"
        assert payload.meta["loop_iteration"] == 42

        # Send notification (disabled mode for test)
        result = send_notification(payload, handler_command="")
        assert result is True

    def test_json_serialization(self):
        """Test that payload can be serialized to JSON."""
        registry = {
            "session1": {"is_alive": False, "last_status": "stopped", "last_log": "Done"},
        }

        payload = create_notification_payload(
            sessions_registry=registry,
            stopped_sessions=["session1"],
            loop_iteration=1,
        )

        # Should not raise
        json_str = json.dumps(payload.to_dict())
        assert isinstance(json_str, str)

        # Should be parseable
        parsed = json.loads(json_str)
        assert parsed["stats"]["total_sessions"] == 1
