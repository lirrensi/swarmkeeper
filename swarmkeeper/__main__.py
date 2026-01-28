"""SwarmKeeper - CLI entry point."""

import argparse
import sys
import os

from swarmkeeper.cli import dump_command, list_command, manager_command, start_command, stop_command
from swarmkeeper.config.manager import load_config

# Force UTF-8 encoding on Windows BEFORE any other imports
if sys.platform == "win32":
    # Change console code page to UTF-8
    os.system("chcp 65001 >nul 2>&1")
    # Reconfigure stdout/stderr to use UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")


def main():
    """Main entry point for SwarmKeeper CLI."""
    # Ensure config exists on any CLI invocation
    load_config()

    parser = argparse.ArgumentParser(
        description="SwarmKeeper - Manage and observe coding agent sessions",
        prog="swarmkeeper",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start command
    start_parser = subparsers.add_parser("start", help="Create new agent session")
    start_parser.add_argument(
        "--name",
        dest="session_name",
        help="Custom name for the session (optional)",
    )
    start_parser.add_argument(
        "cmd",
        nargs="?",
        help="Command to run in session (optional)",
    )

    # list command
    subparsers.add_parser("list", help="Show active sessions")

    # dump command
    subparsers.add_parser("dump", help="Display all session outputs")

    # manager command
    subparsers.add_parser("manager", help="Run manager to check all sessions")

    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a tmux session")
    stop_parser.add_argument(
        "session_name",
        help="Name of the session to stop (e.g., 'agent-01-spider')",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "start":
            session_name = start_command(args.cmd, args.session_name)
            print(f"Created session: {session_name}")

        elif args.command == "list":
            output = list_command()
            print(output)

        elif args.command == "dump":
            outputs = dump_command()
            if outputs:
                for session_name, output in outputs.items():
                    print(f"\n{'=' * 60}")
                    print(f"Session: {session_name}")
                    print(f"{'=' * 60}")
                    print(output)
            else:
                print("No active sessions")

        elif args.command == "manager":
            reports = manager_command()
            if reports:
                print("Session Health Report:")
                print(f"{'-' * 60}")
                for report in reports:
                    status_icon = "[OK]" if report["status"] == "working" else "[X]"
                    print(f"{status_icon} {report['session_name']}")
                    print(f"  Status: {report['status']}")
                    print(f"  Log: {report['log']}")
                    print(f"  Alive: {'Yes' if report['is_alive'] else 'No'}")
                    print()
            else:
                print("No sessions to check")

        elif args.command == "stop":
            output = stop_command(args.session_name)
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
