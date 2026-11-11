"""Jason Stys: actual resource caps and frozen identity failure boundaries. Lines: docs/SOURCE_MAP.md."""

import io
import json
import platform

import pytest

from coordinator import desktop
from coordinator.desktop_profile import PRODUCT


def test_source_mode_is_explicit_and_frozen_missing_identity_fails(tmp_path, monkeypatch):
    """A frozen package cannot silently become an unverified source-mode launch."""
    assert desktop.identity(tmp_path) == {
        "name": PRODUCT,
        "version": "0.2.1",
        "mode": "development",
    }
    monkeypatch.setattr(desktop.sys, "frozen", True, raising=False)
    with pytest.raises(ValueError, match="missing"):
        desktop.identity(tmp_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("name", "another-app"),
        ("version", "0.1.0"),
        ("python_version", "3.14.6"),
        ("source_commit", "invalid"),
        ("source_dirty", "false"),
    ],
)
def test_each_wrong_frozen_identity_surface_is_rejected(tmp_path, field, value):
    """Independent one-field faults fail actual bounded JSON loading without deleting any prior bytes."""
    path = tmp_path / "coordinator/resources/RELEASE.json"
    path.parent.mkdir(parents=True)
    valid = {
        "schema_version": 1,
        "name": PRODUCT,
        "version": "0.2.1",
        "python_version": platform.python_version(),
        "source_commit": "a" * 40,
        "source_dirty": False,
    }
    path.write_text(json.dumps(valid))
    assert desktop.identity(tmp_path) == valid
    path.write_text(json.dumps({**valid, field: value}))
    with pytest.raises(ValueError, match="invalid"):
        desktop.identity(tmp_path)


def test_resources_are_real_regular_nonempty_bounded_files(tmp_path):
    """Actual empty, excessive and directory inputs cannot substitute for packaged HTML/identity."""
    path = tmp_path / "asset"
    path.write_bytes(b"ok")
    assert desktop.read_resource(path) == b"ok"
    for raw in (b"", b"x" * (2 * 1024 * 1024 + 1)):
        path.write_bytes(raw)
        with pytest.raises(ValueError, match="bounded"):
            desktop.read_resource(path)
    with pytest.raises((OSError, ValueError)):
        desktop.read_resource(tmp_path)


def test_console_owner_uses_actual_saved_profile_and_quits_without_password_input(
    tmp_path, monkeypatch, capsys
):
    """The documented console mode runs the same real service and saves no preset account or pipe credential."""
    from coordinator.desktop_profile import FIRST_ROLE, Profile

    path = tmp_path / "profile"
    profile = Profile(path)
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    profile.close()
    monkeypatch.setattr(desktop.sys, "stdin", io.StringIO("unexpected-command\nquit\n"))
    assert desktop.main(["--profile", str(path), "--no-window", "--no-browser"]) == 0
    output = capsys.readouterr().out
    assert "PORTFOLIO_READY " in output and "Unknown owner command" in output
    assert "unexpected-command" not in output and "Synthetic-native-only-2026!" not in output
    reopened = Profile(path)
    try:
        assert reopened.count_users() == 1
    finally:
        reopened.close()


def test_console_cannot_create_preset_first_account(tmp_path):
    """Automation cannot bypass first-owner setup or create a built-in password."""
    from coordinator.desktop_profile import Profile

    path = tmp_path / "profile"
    with pytest.raises(ValueError, match="first account"):
        desktop.console_session(path, {})
    profile = Profile(path)
    try:
        assert profile.count_users() == 0
    finally:
        profile.close()


def test_entrypoint_requires_explicit_console_mode_and_real_resources(
    tmp_path, monkeypatch, capsys
):
    """An invalid CLI or missing packaged UI produces a real failure, never a demo/server fallback."""
    with pytest.raises(SystemExit) as error:
        desktop.main(["--no-window"])
    assert error.value.code == 2
    monkeypatch.setattr(desktop, "ROOT", tmp_path)
    assert (
        desktop.main(["--no-window", "--no-browser", "--profile", str(tmp_path / "profile")]) == 1
    )
    assert "Cannot open local application" in capsys.readouterr().err
    assert not (tmp_path / "profile").exists()


def test_normal_entrypoint_presents_native_controls(tmp_path, monkeypatch):
    """The actual Tk main loop receives this chosen profile/version rather than a prepared scenario launcher."""
    from coordinator import owner_window

    observed = []

    def close_after_construct(root, directory, metadata, *, no_browser):
        from types import SimpleNamespace

        observed.append((directory, metadata, no_browser))
        root.after_idle(root.destroy)
        return SimpleNamespace(exit_code=0)

    monkeypatch.setattr(owner_window, "OwnerWindow", close_after_construct)
    assert desktop.main(["--profile", str(tmp_path / "chosen"), "--no-browser"]) == 0
    assert observed == [
        (tmp_path / "chosen", {"name": PRODUCT, "version": "0.2.1", "mode": "development"}, True)
    ]


def test_actual_loaded_tk_matches_package_and_runtime_info_opens_no_profile(
    tmp_path, monkeypatch, capsys
):
    """The real GUI library pair is checked even by the packaged diagnostic, without user-data initialization."""
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        versions = desktop.inspect_tk(root, {"mode": "development"})
        assert desktop.inspect_tk(root, versions) == versions
        with pytest.raises(ValueError, match="does not match"):
            desktop.inspect_tk(root, {**versions, "tcl_version": "0.0.invalid"})
    finally:
        root.destroy()
    monkeypatch.setattr(
        desktop,
        "default_directory",
        lambda: (_ for _ in ()).throw(AssertionError("diagnostic opened default profile")),
    )
    assert desktop.main(["--runtime-info", "--profile", str(tmp_path / "never-created")]) == 0
    output = capsys.readouterr().out
    record = json.loads(output.split("PORTFOLIO_RUNTIME ", 1)[1])
    assert {name: record[name] for name in versions} == versions
    assert not (tmp_path / "never-created").exists()


def test_console_interrupt_drains_the_actual_owned_host_and_releases_profile(
    tmp_path, monkeypatch, capsys
):
    """A supported Ctrl+C at the owner pipe cannot orphan the real server or retain its file lock."""
    from coordinator.desktop_profile import FIRST_ROLE, Profile

    path = tmp_path / "profile"
    profile = Profile(path)
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    profile.close()
    actual_host = desktop.Host
    observed = []

    def remember(*args):
        host = actual_host(*args)
        observed.append(host)
        return host

    class Interrupted:
        def __iter__(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(desktop, "Host", remember)
    monkeypatch.setattr(desktop.sys, "stdin", Interrupted())
    desktop.console_session(path, {"name": PRODUCT, "version": "0.2.1", "mode": "development"})
    assert (
        len(observed) == 1
        and not observed[0].thread.is_alive()
        and observed[0].listener.fileno() == -1
    )
    reopened = Profile(path)
    reopened.close()
    assert "Owner interrupt received; draining active work." in capsys.readouterr().out
