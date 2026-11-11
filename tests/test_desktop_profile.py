"""Jason Stys: actual private profiles, lock ownership, no reset and real authentication. Lines: docs/SOURCE_MAP.md."""

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from coordinator.api import create_app
from coordinator.desktop_profile import FIRST_ROLE, PRODUCT, Profile, default_directory, read_marker


def test_provision_persist_login_and_existing_roles(tmp_path):
    """The real stored Argon2 account signs into the unchanged API; reopening retains all data."""
    path = tmp_path / "profile"
    profile = Profile(path)
    assert profile.count_users() == 0
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    profile.create_account(
        "reader", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", "observer"
    )
    original = profile.store.snapshot()
    namespace = profile.cookie_name
    marker_bytes = (path / "profile.json").read_bytes()
    with pytest.raises((OSError, ValueError)):
        Profile(path)
    profile.close()
    profile.close()
    with pytest.raises(ValueError, match="closed"):
        profile.create_account("other", "ignored", "ignored", FIRST_ROLE)
    reopened = Profile(path, examples=True)
    try:
        assert reopened.count_users() == 2 and reopened.store.snapshot() == original
        assert (
            reopened.cookie_name == namespace
            and (path / "profile.json").read_bytes() == marker_bytes
        )
        with TestClient(create_app(reopened.store.path)) as client:
            client.base_url = "http://127.0.0.1:8861"
            response = client.post(
                "/api/login",
                headers={"Origin": "http://127.0.0.1:8861"},
                json={"username": "owner", "password": "Synthetic-native-only-2026!"},
            )
            assert response.status_code == 200 and response.json()["role"] == FIRST_ROLE
        with reopened.store.connect() as db:
            values = [tuple(row) for row in db.execute("SELECT * FROM users")]
        assert all("Synthetic-native-only-2026!" not in str(value) for value in values)
    finally:
        reopened.close()


def test_invalid_duplicate_and_first_role_do_not_create_account(tmp_path):
    """Malformed/duplicate requests retain the prior exact user rows instead of overwriting credentials."""
    profile = Profile(tmp_path / "profile")
    try:
        for args in [
            ("owner", "short", "short", FIRST_ROLE),
            ("owner", "long-enough-password", "different-password", FIRST_ROLE),
            ("owner", "long-enough-password", "long-enough-password", "observer"),
        ]:
            with pytest.raises(ValueError):
                profile.create_account(*args)
            assert profile.count_users() == 0
        profile.create_account("owner", "long-enough-password", "long-enough-password", FIRST_ROLE)
        with profile.store.connect() as db:
            original_hash = db.execute(
                "SELECT password_hash FROM users WHERE name = ?", ("owner",)
            ).fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            profile.create_account(
                "owner", "other-long-password", "other-long-password", FIRST_ROLE
            )
        assert profile.count_users() == 1
        with profile.store.connect() as db:
            assert (
                db.execute("SELECT password_hash FROM users WHERE name = ?", ("owner",)).fetchone()[
                    0
                ]
                == original_hash
            )
    finally:
        profile.close()


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"x" * 2049,
        b"not-json",
        b"[]",
        b'{"schema_version":true,"product":"wrong","examples":false}',
    ],
)
def test_invalid_marker_never_adopts_unknown_profile(tmp_path, content):
    """Real malformed/truncated/oversized identity bytes fail before SQLite creates or opens a database."""
    folder = tmp_path / "profile"
    folder.mkdir()
    (folder / "profile.json").write_bytes(content)
    with pytest.raises((ValueError, json.JSONDecodeError)):
        Profile(folder)
    assert not (folder / "workspace.sqlite3").exists()


def test_unknown_folder_and_wrong_product_are_preserved(tmp_path):
    """A user-selected existing folder is never repurposed or reset without the exact product identity."""
    important = tmp_path / "important.txt"
    important.write_text("retain these exact bytes")
    with pytest.raises(ValueError, match="Unknown nonempty"):
        Profile(tmp_path)
    assert (
        important.read_text() == "retain these exact bytes"
        and not (tmp_path / "profile.json").exists()
    )
    important.unlink()
    marker = tmp_path / "profile.json"
    marker.write_text(
        json.dumps({"schema_version": 1, "product": PRODUCT + "-other", "examples": False})
    )
    with pytest.raises(ValueError, match="Unknown profile"):
        read_marker(marker)


def test_default_directory_is_per_user_and_outside_source(monkeypatch, tmp_path):
    """Explicit OS-local data configuration determines persistence; executable CWD never does."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_directory().is_absolute() and default_directory().parts[-2:] == (
        PRODUCT,
        "profile",
    )
