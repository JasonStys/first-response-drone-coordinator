"""Jason Stys: private native-owner profiles and existing-role account provisioning. Lines: docs/SOURCE_MAP.md.

Profile owns one process lock and real SQLite store. Unknown folders are refused;
no HTTP setup endpoint, default credentials or existing-profile reset is introduced.
"""

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

from coordinator.auth import add_user
from coordinator.examples import example
from coordinator.store import Store

PRODUCT = "first-response-drone-coordinator"
ROLES = ("planner", "reviewer", "observer")
FIRST_ROLE = "planner"


def default_directory() -> Path:
    """Keep mutable data outside program/source files in this OS user's application-data area."""
    if sys.platform == "win32":
        base = Path(os.environ["LOCALAPPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    if not base.is_absolute():
        raise ValueError("Application-data directory must be absolute")
    return base / "JasonStysPortfolio" / PRODUCT / "profile"


def read_marker(path: Path) -> dict:
    """Read one regular descriptor with a fixed budget, including growth/truncation checks."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= 2048:
            raise ValueError("Invalid profile identity file")
        raw = stream.read(2049)
    if len(raw) != info.st_size or len(raw) > 2048:
        raise ValueError("Profile identity changed or exceeds its bound")
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "product", "examples"}
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["product"] != PRODUCT
        or type(value["examples"]) is not bool
    ):
        raise ValueError("Unknown profile identity; no migration or reset was attempted")
    return value


class Profile:
    """Exclusive native-owner access; staff permissions remain in the original authenticated API."""

    def __init__(self, directory: Path, *, examples: bool = False):
        """Open only an empty folder or an identified profile; retain its initialization choice."""
        if directory.is_symlink():
            raise ValueError("Choose a real profile directory, not a symbolic link")
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.directory = directory.resolve()
        marker = self.directory / "profile.json"
        if not marker.exists():
            if any(self.directory.iterdir()):
                raise ValueError("Unknown nonempty folder; existing files were not changed")
            with marker.open("x", encoding="utf-8") as stream:
                json.dump({"schema_version": 1, "product": PRODUCT, "examples": examples}, stream)
        metadata = read_marker(marker)
        # Cookie names are public collision namespaces, not credentials. No profile/DB migration is needed.
        namespace = hashlib.sha256(os.path.normcase(str(self.directory)).encode()).hexdigest()[:32]
        self.cookie_name = "response_native_" + namespace
        lock = self.directory / "owner.lock"
        self.descriptor = os.open(
            lock,
            os.O_CREAT | os.O_RDWR | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            if not stat.S_ISREG(os.fstat(self.descriptor).st_mode):
                raise ValueError("Profile lock must be a regular file")
            if os.fstat(self.descriptor).st_size == 0:
                os.write(self.descriptor, b"0")
            os.lseek(self.descriptor, 0, os.SEEK_SET)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self.descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            database = self.directory / "workspace.sqlite3"
            if database.is_symlink():
                raise ValueError("Database must not be a symbolic link")
            self.store = Store(database)
            self.store.initialize(example("wildfire"))
            self.examples = metadata["examples"]
        except BaseException:
            os.close(self.descriptor)
            self.descriptor = -1
            raise

    def count_users(self) -> int:
        """Determine first-account setup without exposing hashes or listing other staff."""
        with self.store.connect() as database:
            return database.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_account(self, username: str, password: str, confirmation: str, role: str):
        """Invoke the same trusted provisioning contract; first account must be the owner setup role."""
        if self.descriptor < 0:
            raise ValueError("Profile has been closed")
        if password != confirmation:
            raise ValueError("Passwords differ")
        if role not in ROLES or (self.count_users() == 0 and role != FIRST_ROLE):
            raise ValueError("First account must use the " + FIRST_ROLE + " role")
        add_user(self.store, username, password, role)

    def close(self):
        """Release only this process's descriptor; never delete the profile, accounts or lock file."""
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1
