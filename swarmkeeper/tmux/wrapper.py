"""Tmux command wrapper."""

import subprocess
import shutil
import platform
from pathlib import Path
from typing import Optional, List, Dict


def get_tmux_path() -> str:
    """Get the path to tmux executable.

    On Windows, looks for psmux/tmux.exe in project directory.
    On Unix, uses system tmux.
    """
    system = platform.system()

    if system == "Windows":
        # Look for psmux/tmux.exe in project directory
        project_root = Path(__file__).parent.parent.parent
        psmux_path = project_root / "psmux" / "tmux.exe"
        if psmux_path.exists():
            return str(psmux_path)

    # Fall back to system tmux
    tmux_path = shutil.which("tmux")
    if tmux_path:
        return tmux_path

    raise RuntimeError("tmux not found. Please install tmux.")


def run_tmux_command(args: list[str]) -> tuple[bool, str, str]:
    """Run a tmux command and return success status, stdout, stderr.

    Args:
        args: List of arguments to pass to tmux

    Returns:
        Tuple of (success, stdout, stderr)
    """
    tmux_path = get_tmux_path()
    cmd = [tmux_path] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def list_sessions() -> List[Dict[str, str]]:
    """List all active tmux sessions with status and last log.

    Returns:
        List of session dictionaries with name, status, and log
    """
    success, stdout, stderr = run_tmux_command(["list-sessions"])

    if not success:
        return []

    # Parse output - handle various tmux formats
    # Windows tmux may not support -F flag, so parse default format
    # Default format: "session-name: N windows (created ...)"
    session_names = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Extract session name - it's the part before the first ":"
        # Handle formats like:
        #   "agent-001: 1 windows (created ...)"
        #   "session-name: 2 windows ..."
        if ":" in line:
            session_name = line.split(":")[0].strip()
            if session_name:
                session_names.append(session_name)
        else:
            # Fallback: if no colon, use whole line
            session_names.append(line)

    # Capture output and analyze for each session
    sessions = []
    for session_name in session_names:
        try:
            # Capture last 10 lines of output
            output = capture_pane(session_name, lines=10)
            # Extract last non-empty line as log
            log_lines = [line.strip() for line in output.split("\n") if line.strip()]
            last_log = log_lines[-1] if log_lines else "No output"

            sessions.append({"name": session_name, "status": "unknown", "log": last_log})
        except Exception:
            # If capture fails, just return basic info
            sessions.append(
                {
                    "name": session_name,
                    "status": "error",
                    "log": "Failed to capture output",
                }
            )

    return sessions


def session_exists(session_name: str) -> bool:
    """Check if specific tmux session exists.

    Args:
        session_name: Name of the tmux session

    Returns:
        True if session exists
    """
    success, _, _ = run_tmux_command(["has-session", "-t", session_name])
    return success


def create_session(session_name: str, command: Optional[str], cwd: str) -> bool:
    """Create new tmux session with optional command.

    On Windows, runs without -d flag in a separate process to allow attachment.
    On Unix, uses -d flag for detached session creation.

    Args:
        session_name: Name for the new session
        command: Command to run in session (optional)
        cwd: Working directory for the session

    Returns:
        True if session created successfully
    """
    import platform

    tmux_path = get_tmux_path()

    # Build command arguments
    args = [
        "new-session",
        "-s",
        session_name,
        "-c",
        cwd,
    ]

    if command:
        args.append(command)

    system = platform.system()

    if system == "Windows":
        # On Windows psmux, -d flag doesn't work properly for persistent sessions
        # Instead, run without -d in a new console window so it attaches naturally
        try:
            cmd = [tmux_path] + args
            # Use CREATE_NEW_CONSOLE to spawn in separate window
            # This allows the session to attach and persist
            subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            # Wait for session to actually exist (with timeout)
            import time

            for _ in range(20):  # Max 2 seconds
                time.sleep(0.1)
                if session_exists(session_name):
                    return True
            return False
        except Exception as e:
            print(f"Failed to create session: {e}")
            return False
    else:
        # On Unix, use -d flag for detached creation
        args.insert(1, "-d")
        success, _, stderr = run_tmux_command(args)

        if not success:
            print(f"Failed to create session: {stderr}")

        return success


def capture_pane(session_name: str, lines: int = 100) -> str:
    """Capture session output (last N lines).

    Args:
        session_name: Name of the tmux session
        lines: Number of lines to capture

    Returns:
        Captured output as string
    """
    success, stdout, stderr = run_tmux_command(
        [
            "capture-pane",
            "-t",
            session_name,
            "-p",  # Print to stdout
            "-S",
            f"-{lines}",  # Start from N lines back
        ]
    )

    if not success:
        return f"[Error capturing session: {stderr}]"

    return stdout


def kill_session(session_name: str) -> bool:
    """Kill tmux session.

    Args:
        session_name: Name of the session to kill

    Returns:
        True if session killed successfully
    """
    success, _, stderr = run_tmux_command(["kill-session", "-t", session_name])

    if not success:
        print(f"Failed to kill session: {stderr}")

    return success


def send_keys(session_name: str, keys: str) -> bool:
    """Send keystrokes to tmux session.

    Args:
        session_name: Name of the tmux session
        keys: Keys to send. Supports:
            - Literal text: "hello world"
            - Special keys: "Enter", "C-c" (Ctrl+C), "C-d" (Ctrl+D)
            - Combinations: "y Enter" (sends 'y' then Enter)

    Returns:
        True if keys sent successfully

    Examples:
        >>> send_keys("my-session", "hello")  # Type "hello"
        >>> send_keys("my-session", "Enter")  # Press Enter
        >>> send_keys("my-session", "C-c")    # Send Ctrl+C
        >>> send_keys("my-session", "y\\n")    # Send 'y' + newline
    """
    # Parse special key sequences
    key_sequence = _parse_key_sequence(keys)

    success, _, stderr = run_tmux_command(["send-keys", "-t", session_name] + key_sequence)

    if not success:
        print(f"Failed to send keys to session: {stderr}")

    return success


def _parse_key_sequence(keys: str) -> list[str]:
    """Parse a key sequence string into tmux send-keys arguments.

    Handles:
    - \\n or Enter -> Enter key
    - \\t or Tab -> Tab key
    - C-x or Ctrl-x -> Ctrl+x
    - M-x or Alt-x -> Alt+x
    - Literal text -> typed as-is

    Args:
        keys: Key sequence string

    Returns:
        List of arguments for tmux send-keys
    """
    result = []
    i = 0

    while i < len(keys):
        char = keys[i]

        # Handle escape sequences
        if char == "\\" and i + 1 < len(keys):
            next_char = keys[i + 1]
            if next_char == "n":
                result.append("Enter")
                i += 2
                continue
            elif next_char == "t":
                result.append("Tab")
                i += 2
                continue
            elif next_char == "\\":
                result.append("\\")
                i += 2
                continue

        # Handle special key names
        remaining = keys[i:]
        if remaining.startswith("Enter") or remaining.startswith("enter"):
            result.append("Enter")
            i += 5
            continue
        elif remaining.startswith("Tab") or remaining.startswith("tab"):
            result.append("Tab")
            i += 3
            continue
        elif remaining.startswith("Space") or remaining.startswith("space"):
            result.append("Space")
            i += 5
            continue

        # Handle Ctrl+ sequences (C-x or Ctrl-x)
        if remaining.upper().startswith("C-") and len(remaining) >= 3:
            ctrl_char = remaining[2].upper()
            if ctrl_char.isalpha() or ctrl_char in "@[\\]^_":
                result.append(f"C-{ctrl_char}")
                i += 3
                continue
        elif remaining.upper().startswith("CTRL-") and len(remaining) >= 6:
            ctrl_char = remaining[5].upper()
            if ctrl_char.isalpha() or ctrl_char in "@[\\]^_":
                result.append(f"C-{ctrl_char}")
                i += 6
                continue

        # Regular character
        result.append(char)
        i += 1

    return result
