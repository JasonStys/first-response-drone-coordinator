"""Jason Stys: acyclic actual GUI-runtime identity checks. Lines: docs/SOURCE_MAP.md.

Shared by owner controls and application entry without importing either launch module.
"""


def inspect_tk(root, metadata: dict) -> dict:
    """Read the actual loaded GUI runtime; a frozen owner window must match its declared Tcl/Tk pair."""
    versions = {
        "tcl_version": str(root.tk.call("info", "patchlevel")),
        "tk_version": str(root.tk.call("package", "require", "Tk")),
    }
    if not all(value.startswith(("8.6.", "9.0.")) for value in versions.values()):
        raise ValueError("Review this Tcl/Tk runtime family before use")
    if metadata.get("mode") != "development" and any(
        metadata.get(name) != value for name, value in versions.items()
    ):
        raise ValueError("Loaded Tcl/Tk does not match this package identity")
    return versions
