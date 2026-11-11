"""Jason Stys: complete local application launch with native owner setup and explicit shutdown. Lines: docs/SOURCE_MAP.md.

Functions: read_resource, identity, console_session, main. Secrets are prompted only
in native widgets or existing trusted CLI; no HTTP signup or preset accounts exist.
"""

import argparse
import json
import os
import platform
import re
import stat
import sys
from pathlib import Path

from coordinator import __version__
from coordinator.desktop_host import Host
from coordinator.desktop_profile import PRODUCT, Profile, default_directory
from coordinator.runtime_gui import inspect_tk

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def read_resource(path: Path) -> bytes:
    """Bound the actual opened regular resource, including growth/truncation, without pathname stat races."""
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 2 * 1024 * 1024:
            raise ValueError("Expected a bounded regular application resource")
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) != info.st_size or len(raw) > 2 * 1024 * 1024:
        raise ValueError("Application resource changed or exceeded its bound")
    return raw


def identity(root: Path) -> dict:
    """A frozen runtime must match its product, version and exact packaged source/runtime declarations."""
    try:
        value = json.loads(read_resource(root / "coordinator/resources/RELEASE.json"))
    except FileNotFoundError:
        if getattr(sys, "frozen", False):
            raise ValueError("Packaged identity missing") from None
        return {"name": PRODUCT, "version": __version__, "mode": "development"}
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value.get("schema_version") != 1
        or value.get("name") != PRODUCT
        or value.get("version") != __version__
        or value.get("python_version") != platform.python_version()
        or not re.fullmatch(r"[a-f0-9]{40}", str(value.get("source_commit", "")))
        or type(value.get("source_dirty")) is not bool
    ):
        raise ValueError("Packaged identity invalid")
    return value


def console_session(directory: Path, metadata: dict):
    """Documented automation/console mode uses the same stored accounts, actual API and graceful owner Quit."""
    profile = Profile(directory)
    host = None
    try:
        if not profile.count_users():
            raise ValueError("Open the native application normally to provision the first account")
        host = Host(profile, metadata)
        try:
            host.start()
            print(
                "Owner control: enter quit or press Ctrl+C. No passwords are accepted on this pipe.",
                flush=True,
            )
            for line in sys.stdin:
                if line.strip() == "quit":
                    break
                print("Unknown owner command; enter quit.", flush=True)
        except KeyboardInterrupt:
            print("Owner interrupt received; draining active work.", flush=True)
    finally:
        try:
            if host is not None:
                host.stop()
        finally:
            if host is None or not host.thread.is_alive():
                profile.close()


def main(argv=None) -> int:
    """Normal launch presents real native setup/Open/Quit controls for the complete existing browser application."""
    parser = argparse.ArgumentParser(
        description="First Response Drone Coordinator desktop by Jason Stys"
    )
    parser.add_argument(
        "--profile", type=Path, help="Identified or new empty private local profile directory"
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--runtime-info",
        action="store_true",
        help="Inspect this actual GUI/runtime package without opening any profile",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Console owner control; requires existing accounts and --no-browser",
    )
    args = parser.parse_args(argv)
    if args.no_window and not args.no_browser:
        parser.error("--no-window requires --no-browser")
    try:
        metadata = identity(ROOT)
        read_resource(ROOT / "dist/index.html")
        if args.runtime_info:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            try:
                versions = inspect_tk(root, metadata)
            finally:
                root.destroy()
            print("PORTFOLIO_RUNTIME " + json.dumps({"package": metadata, **versions}), flush=True)
            return 0
        directory = args.profile or default_directory()
        if args.no_window:
            console_session(directory, metadata)
        else:
            import tkinter as tk

            from coordinator.owner_window import OwnerWindow

            root = tk.Tk()
            window = OwnerWindow(root, directory, metadata, no_browser=args.no_browser)
            while True:
                try:
                    root.mainloop()
                    break
                except KeyboardInterrupt:
                    if window.stop():
                        break
            if window.exit_code:
                return window.exit_code
        print("Application stopped; saved accounts and records retained.", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Cannot open local application: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
