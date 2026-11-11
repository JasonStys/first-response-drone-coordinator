"""Jason Stys: collect real runtime license notices, including DLL-embedded Tcl/Tk9 libraries. Lines: docs/SOURCE_MAP.md."""

import re
from importlib.metadata import distribution
from pathlib import Path


def collect(root: Path) -> tuple[dict, bytes]:
    """Retain every locked Python runtime notice and the actual loaded GUI runtime's bounded license bytes."""
    import tkinter

    window = tkinter.Tk()
    window.withdraw()
    try:
        versions = {
            "tcl_version": str(window.tk.call("info", "patchlevel")),
            "tk_version": str(window.tk.call("package", "require", "Tk")),
        }
        if not all(value.startswith(("8.6.", "9.0.")) for value in versions.values()):
            raise ValueError("Review a different Tcl/Tk family before freezing")
        blocks = []
        for title, library in [
            ("Tcl " + versions["tcl_version"], window.tk.call("info", "library")),
            ("Tk " + versions["tk_version"], window.tk.eval("set tk_library")),
        ]:
            channel = window.tk.call("open", str(library) + "/license.terms", "rb")
            try:
                raw = window.tk.call("read", channel, 65537)
            finally:
                window.tk.call("close", channel)
            raw = raw.encode("utf-8") if isinstance(raw, str) else raw
            if not isinstance(raw, bytes) or not 100 <= len(raw) <= 65536:
                raise ValueError("Actual GUI runtime license is missing or exceeds its byte bound")
            blocks.append((title, raw))
    finally:
        window.destroy()
    blocks.append(("Authored project — MIT", (root / "LICENSE").read_bytes()))
    blocks.append(("Python3.14.10 runtime license", (root / "licenses/PYTHON.txt").read_bytes()))
    names = re.findall(
        r"^([A-Za-z0-9][A-Za-z0-9-]*)==", (root / "requirements.lock").read_text(), re.M
    )
    for name in [*names, "pyinstaller"]:
        info = distribution(name)
        files = [
            info.locate_file(path)
            for path in info.files or []
            if "/licenses/" in str(path).lower()
            or Path(path).name.upper().startswith(("LICENSE", "COPYING", "NOTICE"))
        ]
        if not files:
            raise ValueError("Runtime license notice missing: " + name)
        for path in files:
            with path.open("rb") as stream:
                raw = stream.read(2 * 1024 * 1024 + 1)
            if not 0 < len(raw) <= 2 * 1024 * 1024:
                raise ValueError("Runtime license exceeds its byte bound")
            blocks.append((name + " — " + path.name, raw))
    return versions, b"\n\n".join(title.encode("utf-8") + b"\n" + raw for title, raw in blocks)
