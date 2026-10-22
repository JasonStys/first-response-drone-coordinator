"""Jason Stys: local CLI initialization, interactive account provisioning and loopback server.

Functions/variables and lines: docs/SOURCE_MAP.md. Passwords are read through getpass.
"""

import argparse
import getpass
from pathlib import Path

import uvicorn

from coordinator.api import create_app
from coordinator.auth import add_user
from coordinator.examples import KINDS, example
from coordinator.store import Store


def main():
    """Parse trusted local CLI arguments; never expose an unauthenticated setup endpoint."""
    parser = argparse.ArgumentParser(description="Synthetic first-response planning by Jason Stys")
    parser.add_argument("--db", type=Path, default=Path(".runtime/workspace.db"))
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--scenario", choices=KINDS, default="wildfire")
    user = commands.add_parser("user")
    user.add_argument("name")
    user.add_argument("--role", choices=["planner", "reviewer", "observer"], required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8861)
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == "init":
        store.initialize(example(args.scenario))
        print("Workspace initialized without overwriting existing data; provision users next.")
    elif args.command == "user":
        password = getpass.getpass("New password (14–128 characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords differ")
        add_user(store, args.name, password, args.role)
        print("Account created. Password is not written to source or command history.")
    else:
        if not 1024 <= args.port <= 65535:
            raise SystemExit("Choose a port from 1024 through 65535")
        uvicorn.run(
            create_app(args.db, f"http://127.0.0.1:{args.port}"),
            host="127.0.0.1",
            port=args.port,
            access_log=False,
            limit_concurrency=16,
        )


if __name__ == "__main__":
    main()
