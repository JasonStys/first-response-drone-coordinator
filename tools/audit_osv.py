"""Jason Stys: checksum-pinned official OSV scan with independent full-lockfile coverage gate.

Functions/variables and lines: docs/SOURCE_MAP.md. No ignored findings, offline result
substitution, dependency execution or automatic fixes. Reports remain private runtime data.
"""

import hashlib
import json
import platform
import stat
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v2.7.0"
BINARIES = {
    ("win32", "amd64"): (
        "osv-scanner_windows_amd64.exe",
        "9964ed64ec9a387391eb4cc006ad5c531154821aef29b793e02c448de4686438",
    ),
    ("win32", "arm64"): (
        "osv-scanner_windows_arm64.exe",
        "3e630381c1f1fd3c9c4d447e6ff2ef6c737083371722773db8337eead0f97962",
    ),
    ("linux", "x86_64"): (
        "osv-scanner_linux_amd64",
        "160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b",
    ),
    ("linux", "aarch64"): (
        "osv-scanner_linux_arm64",
        "4061ef4c021ed3c47f203b818f337e351336cc5cd67c0274fc36bd1dfc728dd7",
    ),
    ("darwin", "x86_64"): (
        "osv-scanner_darwin_amd64",
        "e82c5df7ab0a42dff29a1cd0660711447b56b4c0483ff66ad8634df10fd81a45",
    ),
    ("darwin", "arm64"): (
        "osv-scanner_darwin_arm64",
        "d4926ef8da134332543be276dff157e4c170f99ad91fc48e89448a8816bdf70b",
    ),
}


def expected_packages(lock):
    """Extract every resolved dependency identity, including nested and platform-optional entries."""
    if lock.get("lockfileVersion") != 3 or not isinstance(lock.get("packages"), dict):
        raise ValueError("Expected npm lockfile v3")
    expected = set()
    for location, package in lock["packages"].items():
        if not location:
            continue
        name = package.get("name") or location.rsplit("node_modules/", 1)[-1]
        version = package.get("version")
        if (
            not isinstance(name, str)
            or not isinstance(version, str)
            or not name
            or not version
            or package.get("link")
        ):
            raise ValueError(
                "Every dependency must have a resolved name/version, without workspace links"
            )
        expected.add((name, version))
    if not expected:
        raise ValueError("No dependencies to audit")
    return expected


def verify_report(report, expected):
    """Require every expected package and zero findings, independently of scanner's exit code."""
    if (
        not isinstance(report, dict)
        or report.get("errors")
        or not isinstance(report.get("results"), list)
    ):
        raise ValueError("Invalid or incomplete OSV report")
    scanned = set()
    for result in report["results"]:
        source = result.get("source", {})
        if (
            source.get("type") != "lockfile"
            or Path(source.get("path", "")).name != "package-lock.json"
        ):
            raise ValueError("Unexpected report source")
        if not isinstance(result.get("packages"), list):
            raise ValueError("Missing scanned package inventory")
        for item in result["packages"]:
            package = item.get("package", {})
            if (
                package.get("ecosystem") != "npm"
                or not isinstance(package.get("name"), str)
                or not isinstance(package.get("version"), str)
            ):
                raise ValueError("Invalid scanned dependency")
            findings = item.get("vulnerabilities", [])
            if not isinstance(findings, list) or findings or item.get("groups"):
                raise ValueError("OSV findings or malformed vulnerability data: review the report")
            scanned.add((package["name"], package["version"]))
    if not expected.issubset(scanned):
        raise ValueError(f"Incomplete audit: {len(expected - scanned)} locked dependencies missing")
    return len(scanned)


def main():
    """Verify the official binary, query live OSV, require successful exit and complete coverage."""
    name, checksum = BINARIES[(sys.platform, platform.machine().lower())]
    directory = ROOT / ".runtime/osv"
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / name
    if not binary.is_file():
        url = f"https://github.com/google/osv-scanner/releases/download/{VERSION}/{name}"
        with urllib.request.urlopen(url, timeout=60) as response, binary.open("wb") as output:  # noqa: S310 - fixed HTTPS official vendor release URL
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != checksum:
        raise ValueError("OSV binary checksum mismatch; refusing to execute")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    config = ROOT / "tools/osv-scanner.toml"
    if tomllib.loads(config.read_text(encoding="utf-8")) != {}:
        raise ValueError("Advisory suppressions are not allowed")
    expected = expected_packages(
        json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    )
    report = directory / "report.json"
    command = [
        str(binary),
        "scan",
        "source",
        "--lockfile=package-lock.json",
        f"--config={config}",
        "--all-packages",
        "--format=json",
        f"--output-file={report}",
    ]
    result = subprocess.run(command, cwd=ROOT, timeout=180, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"OSV findings or scanner unavailable (exit {result.returncode}); failing closed"
        )
    scanned = verify_report(json.loads(report.read_text(encoding="utf-8")), expected)
    print(
        json.dumps(
            {
                "scanner": f"Google OSV-Scanner {VERSION}",
                "locked_identities": len(expected),
                "scanned_identities": scanned,
                "findings": 0,
                "complete": True,
            }
        )
    )


if __name__ == "__main__":
    main()
