"""Jason Stys: isolated disposable loopback exercise service for browser tests and previews.

Function/variable lines: docs/SOURCE_MAP.md. Public synthetic credentials are ONLY
created in this temporary demo database. No production DB or user is ever reset.
"""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinator.api import create_app
from coordinator.auth import add_user
from coordinator.examples import example


def main():
    """Create an isolated database; its lifetime is this one local preview process."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8861)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Choose a nonprivileged valid port")
    runtime = Path(".runtime")
    runtime.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="demo-", dir=runtime) as directory:
        app = create_app(Path(directory) / "demo.db", f"http://127.0.0.1:{args.port}")
        app.state.store.initialize(example())
        for role in ("planner", "reviewer", "observer"):
            add_user(app.state.store, role, "Synthetic-demo-only-2026!", role)
        print(f"Disposable synthetic demo: http://127.0.0.1:{args.port}")
        print("Users: planner / reviewer / observer. Password: Synthetic-demo-only-2026!")
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, limit_concurrency=16)


if __name__ == "__main__":
    main()
