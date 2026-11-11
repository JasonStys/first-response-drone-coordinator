"""Jason Stys: native OS-owner setup, staff provisioning, full-workspace opening and Quit. Lines: docs/SOURCE_MAP.md.

This window is trusted local administration, not an application role or HTTP
registration endpoint. It never prints, persists plaintext or defaults passwords.
"""

import sqlite3
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from coordinator import __version__
from coordinator.desktop_host import Host
from coordinator.desktop_profile import FIRST_ROLE, ROLES, Profile
from coordinator.runtime_gui import inspect_tk


class OwnerWindow:
    """Keep the owned server/profile alive until explicit successful shutdown, even after browser tabs close."""

    def __init__(self, root, directory: Path, metadata: dict, *, no_browser=False):
        """Build real native controls around the same existing authenticated application."""
        self.root, self.metadata, self.no_browser = root, metadata, no_browser
        self.exit_code = 0
        inspect_tk(root, metadata)
        self.profile = None
        self.host = None
        self.directory = tk.StringVar(value=str(directory))
        self.examples = tk.BooleanVar(value=True)
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirmation = tk.StringVar()
        self.role = tk.StringVar(value=FIRST_ROLE)
        self.status = tk.StringVar(
            value="Open a new empty folder or an existing identified profile."
        )
        root.title("First Response Drone Coordinator — owner controls")
        root.geometry("780x640")
        root.minsize(700, 600)
        root.protocol("WM_DELETE_WINDOW", self.quit)
        shell = ttk.Frame(root, padding=24)
        shell.pack(fill="both", expand=True)
        # Reserve lifecycle controls before variable-height form/status content.
        actions = ttk.Frame(shell)
        actions.pack(fill="x", side="bottom", pady=(12, 0))
        self.browser = ttk.Button(
            actions, text="Open full application", command=self.open_browser, state="disabled"
        )
        self.browser.pack(side="left")
        self.quit_button = ttk.Button(actions, text="Quit application", command=self.quit)
        self.quit_button.pack(side="right")
        content = ttk.Frame(shell)
        content.pack(fill="both", expand=True)
        self.content_canvas = tk.Canvas(content, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.content_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        self.content_canvas.pack(side="left", fill="both", expand=True)
        body = ttk.Frame(self.content_canvas)
        item = self.content_canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind(
            "<Configure>",
            lambda _event: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            ),
        )
        self.content_canvas.bind(
            "<Configure>", lambda event: self.content_canvas.itemconfigure(item, width=event.width)
        )
        ttk.Label(
            body, text="First Response Drone Coordinator", font=("TkDefaultFont", 17, "bold")
        ).pack(anchor="w")
        ttk.Label(body, text=f"Jason Stys · application v{__version__}").pack(
            anchor="w", pady=(5, 16)
        )
        ttk.Label(
            body,
            text="Synthetic planning exercise only. No dispatch, flight authorization or live aircraft.",
            wraplength=600,
        ).pack(anchor="w")
        location = ttk.LabelFrame(body, text="Private local workspace", padding=12)
        location.pack(fill="x", pady=14)
        self.path_entry = ttk.Entry(location, textvariable=self.directory)
        self.path_entry.pack(fill="x")
        self.choose = ttk.Button(
            location, text="Choose profile folder", command=self.choose_directory
        )
        self.choose.pack(side="left", pady=(10, 0))
        self.open_profile_button = ttk.Button(
            location, text="Open private workspace", command=self.open_profile
        )
        self.open_profile_button.pack(side="right", pady=(10, 0))
        account = ttk.LabelFrame(
            body, text="Trusted computer owner · local staff setup", padding=12
        )
        account.pack(fill="x")
        ttk.Label(
            account,
            text="The first account is a planner. Provision a different reviewer for independent review.",
            wraplength=580,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.account_inputs = []
        for index, (caption, variable, secret) in enumerate(
            [
                ("Username (3–40 lowercase letters/digits/hyphens)", self.username, False),
                ("Password (14–128 characters)", self.password, True),
                ("Confirm password", self.confirmation, True),
            ],
            1,
        ):
            ttk.Label(account, text=caption).grid(row=index, column=0, sticky="w", pady=5)
            entry = ttk.Entry(account, textvariable=variable, show="*" if secret else "")
            entry.grid(row=index, column=1, sticky="ew", padx=(12, 0))
            self.account_inputs.append(entry)
        ttk.Label(account, text="Application role").grid(row=4, column=0, sticky="w", pady=5)
        self.roles = ttk.Combobox(account, textvariable=self.role, values=ROLES, state="disabled")
        self.roles.grid(row=4, column=1, sticky="ew", padx=(12, 0))
        self.create = ttk.Button(
            account,
            text="Create local staff account",
            command=self.create_account,
            state="disabled",
        )
        self.create.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        account.columnconfigure(1, weight=1)
        ttk.Label(
            body,
            text="Account creation is available only in these native owner controls. Browser roles stay unchanged. The trusted OS owner can read the local database; it is not encrypted against them.",
            wraplength=600,
        ).pack(anchor="w", pady=12)
        ttk.Label(body, textvariable=self.status, wraplength=600).pack(anchor="w", pady=(0, 10))
        if (directory / "profile.json").is_file():
            root.after_idle(self.open_profile)

    def choose_directory(self):
        """Let the owner select a normal profile directory; Profile still rejects unknown existing files."""
        selected = filedialog.askdirectory(
            parent=self.root, title="Choose a new empty or existing identified profile folder"
        )
        if selected:
            self.directory.set(selected)

    def open_profile(self):
        """Open/initialize exactly the chosen local profile; no accounts are created automatically."""
        if self.profile is not None:
            return
        try:
            self.profile = Profile(Path(self.directory.get()), examples=self.examples.get())
            for control in (self.path_entry, self.choose, self.open_profile_button):
                control.configure(state="disabled")
            self.create.configure(state="normal")
            if self.profile.count_users():
                self.roles.configure(state="readonly")
                self.start_host()
            else:
                self.status.set("Create your first planner account. No default credentials exist.")
        except (OSError, ValueError, sqlite3.Error, RuntimeError):
            self.status.set(
                "The local profile is open but its service could not start. Quit and reopen this application; saved records were retained."
                if self.profile is not None
                else "Could not open that profile. Unsafe paths, unknown files, a running owner, or an invalid identity were not adopted. Choose another empty folder or check the local console."
            )

    def create_account(self):
        """Clear plaintext widgets after every attempt; existing usernames/roles use the original validation."""
        if self.profile is None:
            return
        try:
            self.profile.create_account(
                self.username.get(), self.password.get(), self.confirmation.get(), self.role.get()
            )
            self.username.set("")
            self.roles.configure(state="readonly")
            self.start_host()
            self.status.set(
                "Local account created. Use it in the full application; additional staff can be provisioned here."
            )
        except sqlite3.IntegrityError:
            self.status.set("That username already exists; its password and role were not changed.")
        except (OSError, ValueError, sqlite3.Error, RuntimeError) as error:
            self.status.set(str(error))
        finally:
            self.password.set("")
            self.confirmation.set("")

    def start_host(self):
        """Start only once and open the actual workspace after real service readiness and a provisioned account."""
        if self.host is None:
            self.host = Host(self.profile, self.metadata)
            self.host.start()
            self.browser.configure(state="normal")
            self.status.set(
                "Workspace ready. Keep these owner controls open; closing a browser tab does not stop it."
            )
            if not self.no_browser:
                self.open_browser()

    def open_browser(self):
        """A normal user action opens this owned full application, never a prepared demo or adopted server."""
        if self.host is not None and self.host.server.started and not self.host.server.should_exit:
            webbrowser.open(self.host.origin + "/")

    def quit(self):
        """Never force termination or release the profile while active service work is still draining."""
        if not messagebox.askyesno(
            "Quit application",
            "Stop this application's local service? Saved accounts and records will be retained.",
            parent=self.root,
        ):
            return
        self.stop()

    def stop(self) -> bool:
        """Complete an explicit Quit/Ctrl+C; an already failed stopped service can close honestly with exit1."""
        try:
            if self.host is not None:
                self.host.stop()
        except RuntimeError as error:
            self.status.set(str(error))
            if self.host is not None and self.host.thread.is_alive():
                return False
            self.exit_code = 1
        if self.profile is not None:
            self.profile.close()
        self.root.destroy()
        return True
