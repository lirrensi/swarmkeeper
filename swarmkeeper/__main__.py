"""SwarmKeeper - CLI entry point."""

import argparse
import sys
import os

from swarmkeeper.cli import (
    dump_command,
    list_command,
    manager_command,
    manager_loop_command,
    pattern_command,
    pattern_loop_command,
    start_command,
    stop_command,
)
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
    manager_parser = subparsers.add_parser("manager", help="Run manager to check all sessions")

    # manager-loop command
    manager_loop_parser = subparsers.add_parser("manager-loop", help="Run continuous manager loop")
    manager_loop_parser.add_argument(
        "--interval",
        type=int,
        default=180,
        help="Check interval in seconds (default: 180)",
    )
    manager_loop_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Require 2 consecutive checks before stopping",
    )
    manager_loop_parser.add_argument(
        "--notify-handler",
        dest="notify_handler",
        default=None,
        help="Notification handler: path to script (custom), empty string (disabled), or omit (OS default)",
    )

    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a tmux session")
    stop_parser.add_argument(
        "session_name",
        help="Name of the session to stop (e.g., 'agent-01-spider')",
    )

    # pattern command
    pattern_parser = subparsers.add_parser("pattern", help="Pattern-based check on all sessions")
    pattern_parser.add_argument(
        "--string",
        dest="patterns",
        action="append",
        required=True,
        help="Pattern to search for (can be specified multiple times)",
    )
    pattern_parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat patterns as regular expressions",
    )
    pattern_parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Enable fuzzy matching (ignores extra spaces, case insensitive)",
    )
    pattern_parser.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=80.0,
        help="Fuzzy match threshold 0-100 (default: 80)",
    )
    pattern_parser.add_argument(
        "--lines",
        type=int,
        default=100,
        help="Number of lines to check (default: 100)",
    )

    # pattern-loop command
    pattern_loop_parser = subparsers.add_parser(
        "pattern-loop", help="Run continuous pattern monitoring loop"
    )
    pattern_loop_parser.add_argument(
        "--string",
        dest="patterns",
        action="append",
        required=True,
        help="Pattern to search for (can be specified multiple times)",
    )
    pattern_loop_parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat patterns as regular expressions",
    )
    pattern_loop_parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Enable fuzzy matching (ignores extra spaces, case insensitive)",
    )
    pattern_loop_parser.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=80.0,
        help="Fuzzy match threshold 0-100 (default: 80)",
    )
    pattern_loop_parser.add_argument(
        "--lines",
        type=int,
        default=100,
        help="Number of lines to check (default: 100)",
    )
    pattern_loop_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    pattern_loop_parser.add_argument(
        "--auto-type",
        dest="auto_type",
        default=None,
        help="Keys to send when pattern detected (e.g., 'y\\n' for 'y' + Enter)",
    )
    pattern_loop_parser.add_argument(
        "--auto-type-max",
        type=int,
        default=2,
        help="Max auto-type interventions per session (default: 2)",
    )
    pattern_loop_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Require 2 consecutive detections before action",
    )
    pattern_loop_parser.add_argument(
        "--notify-handler",
        dest="notify_handler",
        default=None,
        help="Notification handler: path to script (custom), empty string (disabled), or omit (OS default)",
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

        elif args.command == "manager-loop":
            manager_loop_command(
                interval=args.interval, confirm=args.confirm, notify_handler=args.notify_handler
            )

        elif args.command == "stop":
            output = stop_command(args.session_name)
            print(output)

        elif args.command == "pattern":
            results = pattern_command(
                patterns=args.patterns,
                use_regex=args.regex,
                use_fuzzy=args.fuzzy,
                fuzzy_threshold=args.fuzzy_threshold,
                lines=args.lines,
            )
            if results:
                print("Pattern Check Results:")
                print(f"{'-' * 60}")
                any_matched = False
                for result in results:
                    if result["matched"]:
                        any_matched = True
                        print(f"[MATCH] {result['session_name']}")
                        print(f"  Pattern: {result['matched_pattern']}")
                        print(f"  Text: {result['matched_text'][:100]}...")
                    else:
                        status = "[DEAD]" if not result["is_alive"] else "[NO MATCH]"
                        print(f"{status} {result['session_name']}")
                    print()
                # Exit with error code if no matches
                if not any_matched:
                    sys.exit(1)
            else:
                print("No sessions to check")
                sys.exit(1)

        elif args.command == "pattern-loop":
            pattern_loop_command(
                patterns=args.patterns,
                use_regex=args.regex,
                use_fuzzy=args.fuzzy,
                fuzzy_threshold=args.fuzzy_threshold,
                lines=args.lines,
                interval=args.interval,
                auto_type=args.auto_type,
                auto_type_max=args.auto_type_max,
                confirm=args.confirm,
                notify_handler=args.notify_handler,
            )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
