"""Tests for manager loop control."""

import pytest
from unittest.mock import patch
from swarmkeeper.manager.loop import run_loop


class TestRunLoop:
    """Test suite for run_loop function."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock sessions registry."""
        return {
            "agent-01-spider": {
                "created": "2026-01-28T00:00:00",
                "command": "echo hello",
                "checks": [],
            },
            "agent-02-bear": {
                "created": "2026-01-28T01:00:00",
                "command": "python task.py",
                "checks": [],
            },
        }

    @pytest.fixture
    def mock_run_manager(self):
        """Mock the run_manager function."""
        with patch("swarmkeeper.manager.loop.run_manager") as mock:
            yield mock

    def test_stops_on_first_stopped_session(self, mock_registry, mock_run_manager):
        """Test that loop stops immediately on first stopped session (fast mode)."""
        # Create a stopped session
        mock_registry["agent-01-spider"]["is_alive"] = False
        mock_registry["agent-01-spider"]["last_status"] = "stopped"
        mock_registry["agent-01-spider"]["last_log"] = "Session stopped"

        # Mock manager to return stopped session
        mock_run_manager.return_value = mock_registry

        with patch("time.sleep"):
            result = run_loop(mock_registry, interval_seconds=60)

            # Verify manager was called once and loop stopped
            assert mock_run_manager.call_count == 1
            assert result is mock_registry

    def test_confirms_on_second_stopped_session(self, mock_registry, mock_run_manager):
        """Test that loop requires 2 consecutive checks in confirmation mode."""
        # First call: stopped session detected
        mock_run_manager.side_effect = [mock_registry, mock_registry]
        mock_registry["agent-01-spider"]["is_alive"] = False
        mock_registry["agent-01-spider"]["last_status"] = "stopped"
        mock_registry["agent-01-spider"]["last_log"] = "Session stopped"

        with patch("time.sleep") as mock_sleep:
            result = run_loop(mock_registry, interval_seconds=0.1, require_confirmation=True)

            # Verify manager was called twice
            assert mock_run_manager.call_count == 2
            # Verify sleep was called between checks
            mock_sleep.assert_called_once()
            assert result is mock_registry

    def test_continues_with_all_working_sessions(self, mock_registry, mock_run_manager):
        """Test that loop continues when all sessions are working."""
        # All sessions are alive
        mock_run_manager.return_value = mock_registry

        with patch("time.sleep"):
            result = run_loop(mock_registry, interval_seconds=1)

            # Verify manager was called
            assert mock_run_manager.call_count >= 1
            assert result is mock_registry

    def test_empty_registry(self, mock_run_manager):
        """Test that loop exits immediately with empty registry."""
        empty_registry = {}

        with patch("time.sleep"):
            result = run_loop(empty_registry, interval_seconds=60)

            # Verify manager was called once
            assert mock_run_manager.call_count == 1
            assert result == {}

    def test_keyboard_interrupt_handling(self, mock_registry, mock_run_manager):
        """Test that KeyboardInterrupt is handled gracefully."""
        # Mock manager to raise KeyboardInterrupt
        mock_run_manager.side_effect = KeyboardInterrupt()

        with patch("swarmkeeper.manager.loop.save_sessions") as mock_save:
            # Run loop
            with pytest.raises(KeyboardInterrupt):
                run_loop(mock_registry, interval_seconds=60)

            # Verify save_sessions was called on interrupt
            mock_save.assert_called_once_with(mock_registry)

    def test_exception_handling(self, mock_registry, mock_run_manager):
        """Test that exceptions are handled gracefully."""
        # Mock manager to raise an exception
        mock_run_manager.side_effect = Exception("Test error")

        with patch("swarmkeeper.manager.loop.save_sessions") as mock_save:
            # Run loop
            with pytest.raises(Exception):
                run_loop(mock_registry, interval_seconds=60)

            # Verify save_sessions was called on exception
            mock_save.assert_called_once_with(mock_registry)
