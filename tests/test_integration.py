"""Integration tests for SwarmKeeper."""

import subprocess
import time
import unittest
from pathlib import Path

from swarmkeeper.cli import dump_command, list_command, start_command
from swarmkeeper.tmux.wrapper import kill_session, session_exists


class TestSwarmKeeperIntegration(unittest.TestCase):
    """Integration tests for SwarmKeeper functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_sessions = []

    def tearDown(self):
        """Clean up test sessions."""
        for session_name in self.test_sessions:
            if session_exists(session_name):
                kill_session(session_name)

    def test_create_and_list_session(self):
        """Test creating a session and listing it."""
        # Create a test session
        session_name = start_command("echo 'test'")
        self.test_sessions.append(session_name)

        # Give tmux a moment to create the session
        time.sleep(0.5)

        # List sessions
        output = list_command()

        # Verify output contains session name
        self.assertIn(session_name, output)

    def test_dump_session_output(self):
        """Test dumping session output."""
        # Create a test session with a command that produces output
        session_name = start_command("echo 'Hello from test'")
        self.test_sessions.append(session_name)

        # Give tmux a moment to create the session and run command
        time.sleep(0.5)

        # Dump outputs
        outputs = dump_command()

        # Verify session output exists
        self.assertIn(session_name, outputs)

    def test_session_cleanup(self):
        """Test that sessions can be cleaned up."""
        # Create a test session
        session_name = start_command("sleep 10")
        self.test_sessions.append(session_name)

        # Give tmux a moment to create the session
        time.sleep(0.5)

        # Verify session exists
        self.assertTrue(session_exists(session_name))

        # Kill session
        kill_session(session_name)

        # Verify session no longer exists
        self.assertFalse(session_exists(session_name))


class TestTmuxWrapper(unittest.TestCase):
    """Tests for tmux wrapper functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_sessions = []

    def tearDown(self):
        """Clean up test sessions."""
        for session_name in self.test_sessions:
            if session_exists(session_name):
                kill_session(session_name)

    def test_create_and_kill_session(self):
        """Test creating and killing a tmux session."""
        from swarmkeeper.tmux.wrapper import create_session

        session_name = "test-session-123"
        self.test_sessions.append(session_name)

        # Create session
        success = create_session(session_name, None, str(Path.cwd()))
        self.assertTrue(success)

        # Verify session exists
        self.assertTrue(session_exists(session_name))

        # Kill session
        kill_session(session_name)
        self.test_sessions.remove(session_name)

        # Verify session no longer exists
        self.assertFalse(session_exists(session_name))

    def test_capture_pane(self):
        """Test capturing pane output."""
        from swarmkeeper.tmux.wrapper import capture_pane, create_session

        session_name = "test-capture-456"
        self.test_sessions.append(session_name)

        # Create session with a command
        success = create_session(session_name, "echo 'capture test'", str(Path.cwd()))
        self.assertTrue(success)

        # Give command time to execute
        time.sleep(0.5)

        # Capture output
        output = capture_pane(session_name, lines=10)

        # Verify we got some output
        self.assertIsInstance(output, str)


if __name__ == "__main__":
    unittest.main()
