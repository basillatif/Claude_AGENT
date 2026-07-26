"""CLI entrypoint for agent-sandbox.

Usage:
    python main.py "your task here"
    python main.py                # interactive prompt
    python main.py "task" --max-turns 20
"""

import argparse
import sys

from dotenv import load_dotenv

from agent import run_agent

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the agent-sandbox agent loop on a task."
    )
    parser.add_argument(
        "task", nargs="?", help="The task to give the agent. Omit for interactive mode."
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Maximum number of agent loop turns before giving up (default: 10)",
    )
    args = parser.parse_args()

    task = args.task
    if not task:
        print("agent-sandbox interactive mode (Ctrl+C to exit)")
        try:
            task = input("Task: ")
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)

    if not task.strip():
        print("No task given.")
        sys.exit(1)

    result = run_agent(task, max_turns=args.max_turns)
    print("\n=== Final response ===")
    print(result)


if __name__ == "__main__":
    main()
