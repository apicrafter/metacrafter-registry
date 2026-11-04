#!/usr/bin/env python
"""Legacy entry point kept for existing docs and habits.

Every command delegates to the `metacrafter-registry` package CLI
(`pip install -e .`, then `metacrafter-registry --help`).
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
COMMANDS = ("build", "validate", "stats", "report", "migrate")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("usage: builder.py {%s} [options]" % "|".join(COMMANDS))
        print("Same as: metacrafter-registry <command> (see metacrafter-registry --help)")
        raise SystemExit(0 if len(sys.argv) < 2 else 2)
    try:
        from metacrafter_registry.cli import main as cli_main
    except ImportError:
        sys.path.insert(0, os.path.join(BASE_DIR, "..", "src"))
        from metacrafter_registry.cli import main as cli_main
    raise SystemExit(cli_main(["--data-dir", DATA_PATH, *sys.argv[1:]]))


if __name__ == "__main__":
    main()
