"""Jason Stys: real Tk control bindings with fresh profiles and actual authenticated service. Lines: docs/SOURCE_MAP.md."""

import tkinter as tk

import pytest

from coordinator import owner_window
from coordinator.desktop_profile import FIRST_ROLE, PRODUCT, Profile


@pytest.fixture
def window(tmp_path):
    """Construct actual widgets (Xvfb on headless Linux), never an unrelated user profile or display fixture."""
    root = tk.Tk()
    root.withdraw()
    view = owner_window.OwnerWindow(
        root,
        tmp_path / "profile",
        {"name": PRODUCT, "version": "0.2.1", "mode": "development"},
        no_browser=True,
    )
    yield root, view
    if view.host is not None and view.host.thread.is_alive():
        view.host.stop()
    if view.profile is not None:
        view.profile.close()
    try:
        root.destroy()
    except tk.TclError:
        pass  # A tested successful owner Quit has already destroyed this exact root.


def credentials(view, name, password=None, confirmation=None):
    """Drive actual Tk variables feeding the button's real native provisioning handler."""
    password = "Synthetic-native-only-2026!" if password is None else password
    view.username.set(name)
    view.password.set(password)
    view.confirmation.set(password if confirmation is None else confirmation)


def test_actual_buttons_first_account_staff_and_no_password_retention(window, monkeypatch):
    """The real command bindings preserve first-role setup and duplicate credentials, then open the owned full GUI."""
    _, view = window
    opened = []
    monkeypatch.setattr(owner_window.webbrowser, "open", lambda url: opened.append(url))
    view.create_account()
    view.open_browser()
    view.open_profile_button.invoke()
    assert view.profile.count_users() == 0 and view.host is None
    assert str(view.roles["state"]) == "disabled"
    credentials(view, "owner", confirmation="different")
    view.create.invoke()
    assert (
        view.status.get() == "Passwords differ"
        and not view.password.get()
        and not view.confirmation.get()
    )
    assert view.profile.count_users() == 0
    credentials(view, "owner")
    view.create.invoke()
    assert view.profile.count_users() == 1 and view.host.server.started
    assert not opened and str(view.roles["state"]) == "readonly"
    original_host = view.host
    view.open_profile()
    view.browser.invoke()
    assert opened == [view.host.origin + "/"]
    credentials(view, "reader")
    view.role.set("observer")
    view.create.invoke()
    assert view.profile.count_users() == 2 and view.host is original_host
    credentials(view, "owner", password="different-valid-password")
    view.role.set(FIRST_ROLE)
    view.create.invoke()
    assert "already exists" in view.status.get() and view.profile.count_users() == 2
    assert not view.password.get() and not view.confirmation.get()


def test_folder_choice_and_unknown_existing_files_are_not_adopted(window, tmp_path, monkeypatch):
    """Cancelled selection retains the path; a chosen nonempty folder cannot be repurposed by the native button."""
    _, view = window
    original = view.directory.get()
    monkeypatch.setattr(owner_window.filedialog, "askdirectory", lambda **_: "")
    view.choose.invoke()
    assert view.directory.get() == original
    target = tmp_path / "important"
    target.mkdir()
    note = target / "keep.txt"
    note.write_text("unchanged user bytes")
    monkeypatch.setattr(owner_window.filedialog, "askdirectory", lambda **_: str(target))
    view.choose.invoke()
    view.open_profile_button.invoke()
    assert view.profile is None and "not adopted" in view.status.get()
    assert note.read_text() == "unchanged user bytes" and not (target / "profile.json").exists()


def test_cancelled_or_busy_quit_retains_owner_until_actual_completion(window, monkeypatch):
    """A native cancellation or reported drain failure cannot destroy the window or unlock the profile."""
    root, view = window
    view.open_profile_button.invoke()
    credentials(view, "owner")
    view.create.invoke()
    monkeypatch.setattr(owner_window.messagebox, "askyesno", lambda *_args, **_kwargs: False)
    view.quit()
    assert root.winfo_exists() and view.host.thread.is_alive()
    monkeypatch.setattr(owner_window.messagebox, "askyesno", lambda *_args, **_kwargs: True)

    def busy():
        raise RuntimeError("Still draining actual work")

    with monkeypatch.context() as change:
        change.setattr(view.host, "stop", busy)
        view.quit()
        assert "Still draining" in view.status.get() and root.winfo_exists()
        with pytest.raises((OSError, ValueError)):
            Profile(view.profile.directory)
    view.quit()
    assert not view.host.thread.is_alive() and view.profile.descriptor == -1


def test_identified_profile_automatically_reopens_without_reset(tmp_path, monkeypatch):
    """A normal later launch can open the saved full workspace; accounts and domain records survive."""
    path = tmp_path / "profile"
    profile = Profile(path)
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    before = profile.store.snapshot()
    profile.close()
    opened = []
    monkeypatch.setattr(owner_window.webbrowser, "open", lambda url: opened.append(url))
    root = tk.Tk()
    root.withdraw()
    view = owner_window.OwnerWindow(
        root, path, {"name": PRODUCT, "version": "0.2.1", "mode": "development"}
    )
    try:
        root.update()
        assert view.profile.count_users() == 1 and view.profile.store.snapshot() == before
        assert opened == [view.host.origin + "/"]
        assert view.password.get() == view.confirmation.get() == ""
    finally:
        if view.host is not None:
            view.host.stop()
        if view.profile is not None:
            view.profile.close()
        root.destroy()


def test_quit_after_real_startup_failure_releases_owner_and_retains_failure_exit(
    tmp_path, monkeypatch
):
    """A stopped failed server is not active work; the native window can close with an honest error result."""
    path = tmp_path / "profile"
    profile = Profile(path)
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    profile.close()
    actual_host = owner_window.Host

    def failed_host(*args):
        host = actual_host(*args)

        def fail(*_args, **_kwargs):
            raise RuntimeError("synthetic startup failure")

        host.server.run = fail
        return host

    monkeypatch.setattr(owner_window, "Host", failed_host)
    monkeypatch.setattr(owner_window.messagebox, "askyesno", lambda *_args, **_kwargs: True)
    root = tk.Tk()
    root.withdraw()
    view = owner_window.OwnerWindow(root, path, {"mode": "development"}, no_browser=True)
    root.update()
    assert view.host.error is not None and not view.host.thread.is_alive()
    view.quit()
    assert view.exit_code == 1 and view.profile.descriptor == -1


def test_minimum_window_keeps_lifecycle_controls_visible_and_long_status_scrollable(window):
    """Actual Tk geometry keeps Quit available at minimum size, including a long service-drain message."""
    root, view = window
    root.geometry("700x600")
    view.status.set("Still draining active work; wait and choose Quit again. " * 8)
    root.deiconify()
    root.update()
    for control in (view.browser, view.quit_button):
        top = control.winfo_rooty() - root.winfo_rooty()
        assert control.winfo_viewable() and control.winfo_height() > 1
        assert 0 <= top < top + control.winfo_height() <= root.winfo_height()
    assert view.content_canvas.yview()[1] < 1
    view.content_canvas.yview_moveto(1)
    root.update()
    assert view.content_canvas.yview()[1] == 1
    assert view.quit_button.winfo_viewable()
