"""Entry point for the modern planner Tkinter application."""
from __future__ import annotations

import argparse

from planner.export import dump_raw_code
from planner.gui import launch_app


def main() -> None:
    """Launch the graphical planner application or export raw code."""

    parser = argparse.ArgumentParser(description="Modern Planner application")
    parser.add_argument(
        "--dump",
        action="store_true",
        help="print all planner source code and exit",
    )
    args = parser.parse_args()

    if args.dump:
        print(dump_raw_code(), end="")
        return

    launch_app()


if __name__ == "__main__":
    main()
