"""Jason Stys: actual frozen pre-mutation path refusals in owned empty fixtures. Lines: docs/SOURCE_MAP.md."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def snapshot(root: Path) -> dict:
    """Hash only the known installed program tree or a real owned fixture, never an alias target."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def verify(executable: Path, output: Path, environment: dict):
    """The actual frozen program must reject these paths before any profile/program/target writes."""
    fixture = output / "profile-admission"
    fixture.mkdir()
    before_program = snapshot(executable.parent)
    selections = [
        ("inside-program-root", executable.parent / "refused-profile-fixture"),
        ("inside-internal-root", executable.parent / "_internal/refused-profile-fixture"),
    ]
    for label in ("final-alias", "ancestor-alias"):
        folder = fixture / label
        folder.mkdir()
        target = folder / "empty-target"
        target.mkdir()
        alias = folder / "selected-alias"
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(target), str(alias))
            if not alias.is_junction():
                raise ValueError("Actual Windows junction missing")
        else:
            alias.symlink_to(target, target_is_directory=True)
        selections.append((label, alias if label == "final-alias" else alias / "new/profile"))
    results = []
    for label, selected in selections:
        result = subprocess.run(
            [str(executable), "--profile", str(selected), "--no-window", "--no-browser"],
            cwd=output,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        if result.returncode != 1 or "Unsafe profile" not in result.stderr:
            raise ValueError(f"Actual frozen path refusal missing: {label}: {result.returncode}")
        if selected.exists():
            if label.startswith("inside-") or list((fixture / label / "empty-target").iterdir()):
                raise ValueError(f"Refused profile unexpectedly wrote files: {label}")
        results.append(
            {"case": label, "exit_code": result.returncode, "refused_before_mutation": True}
        )
    if snapshot(executable.parent) != before_program:
        raise ValueError("Profile refusal changed installed application files")
    for label in ("final-alias", "ancestor-alias"):
        if list((fixture / label / "empty-target").iterdir()):
            raise ValueError("Profile alias target changed")
    (output / "profile-admission.json").write_text(
        json.dumps(
            {
                "actual_frozen_executable": True,
                "program_files_unchanged": True,
                "cases": results,
                "limit": "Static admission for trusted OS-owner mistakes, not an atomic namespace against concurrent same-user replacement.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
