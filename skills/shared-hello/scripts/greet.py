#!/usr/bin/env python3
"""A tiny greeting helper used by the shared-hello skill."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a friendly greeting.")
    parser.add_argument("--name", default="friend", help="Name to greet.")
    args = parser.parse_args()
    print(f"Hello, {args.name}! Greetings from the shared-hello skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
