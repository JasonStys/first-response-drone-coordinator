"""Jason Stys: actual extracted full application, private synthetic profile, GUI workflow and owner shutdown. Lines: docs/SOURCE_MAP.md."""

import argparse
import http.client
import json
import os
import queue
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

if not __debug__:
    raise RuntimeError("Native acceptance refuses optimized Python")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def require(condition, message):
    """Keep acceptance decisions active even if a caller attempts Python optimization."""
    if not condition:
        raise ValueError(message)


def request(url, path, *, method="GET", headers=None, body=None):
    """Use only a nonce-verified owned loopback authority, with no proxy or redirect behavior."""
    target = urlsplit(url)
    require(
        target.scheme == "http"
        and target.hostname == "127.0.0.1"
        and target.port
        and not target.username
        and target.path == "/",
        "Unexpected application URL",
    )
    connection = http.client.HTTPConnection("127.0.0.1", target.port, timeout=6)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read(262145)
        require(
            len(raw) <= 262144 and not 300 <= response.status < 400,
            "Unexpected response size or redirect",
        )
        return response.status, raw
    finally:
        connection.close()


def main(argv=None):
    """Use the actual archive executable, never source service, default profile, known password or existing listener."""
    from coordinator.desktop import read_resource
    from coordinator.desktop_profile import PRODUCT, ROLES, Profile

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    executable = args.executable.resolve()
    expected = json.loads(read_resource(executable.parent / "RELEASE.json"))
    require(expected["name"] == PRODUCT and expected["version"] == "0.2.0", "Wrong application")
    require(re.fullmatch(r"[a-f0-9]{40}", expected["source_commit"]), "Invalid source identity")
    require(
        json.loads(
            read_resource(executable.parent / "_internal/coordinator/resources/RELEASE.json")
        )
        == expected,
        "Inner/outer source identity differs",
    )
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    node = shutil.which("node")
    require(node, "QA Node runtime missing")
    profile_directory = output / "synthetic-profile"
    password = secrets.token_urlsafe(24)
    profile = Profile(profile_directory, examples=True)
    expected_cookie = profile.cookie_name
    try:
        for role in ROLES:
            profile.create_account(role, password, password, role)
    finally:
        profile.close()
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "SYSTEMDRIVE",
        "TEMP",
        "TMP",
        "PATHEXT",
        "HOME",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "LANG",
        "LC_ALL",
        "DISPLAY",
        "XAUTHORITY",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    environment["PATH"] = (
        os.pathsep.join(
            [str(Path(os.environ["SYSTEMROOT"]) / "System32"), os.environ["SYSTEMROOT"]]
        )
        if os.name == "nt"
        else "/usr/bin:/bin"
    )
    environment["PORTABLE_SMOKE_NONCE"] = secrets.token_hex(24)
    diagnostic = subprocess.run(
        [str(executable), "--runtime-info"],
        cwd=output,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    lines = [
        line for line in diagnostic.stdout.splitlines() if line.startswith("PORTFOLIO_RUNTIME ")
    ]
    require(len(lines) == 1, "Actual frozen GUI runtime diagnostic missing")
    actual_runtime = json.loads(lines[0].removeprefix("PORTFOLIO_RUNTIME "))
    require(
        actual_runtime["package"] == expected
        and all(actual_runtime[key] == expected[key] for key in ("tcl_version", "tk_version")),
        "Actual loaded frozen Tcl/Tk differs",
    )
    (output / "runtime.json").write_text(json.dumps(actual_runtime, indent=2) + "\n")
    process = subprocess.Popen(
        [str(executable), "--profile", str(profile_directory), "--no-window", "--no-browser"],
        cwd=output,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    events = queue.Queue()
    log = []

    def read_output():
        """Observe this exact process's readiness/EOF without guessing ports or accepting old liveness."""
        try:
            for line in process.stdout:
                log.append(line)
                events.put(line)
        finally:
            events.put(None)

    reader = threading.Thread(target=read_output, name="native-acceptance-output", daemon=True)
    reader.start()
    passed, forced, actual_exit, url = False, False, None, None
    try:
        deadline = time.monotonic() + 20
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "Actual native readiness deadline exceeded")
            line = events.get(timeout=remaining)
            require(line is not None, "Actual native process ended before readiness")
            if line.startswith("PORTFOLIO_READY "):
                ready = json.loads(line.removeprefix("PORTFOLIO_READY "))
                break
        require(
            ready["package"] == expected
            and ready["instance"] == environment["PORTABLE_SMOKE_NONCE"],
            "Wrong actual launch source or nonce",
        )
        url = ready["url"]
        code, raw = request(url, "/healthz")
        require(
            code == 200 and json.loads(raw)["desktop"] == ready,
            "Actual API readiness identity differs",
        )
        require(request(url, "/api/workspace")[0] == 401, "Anonymous workspace disclosure")
        require(
            request(url, "/healthz", headers={"Host": "foreign.invalid"})[0] == 400,
            "Foreign authority accepted",
        )
        require(
            request(
                url,
                "/api/login",
                method="POST",
                headers={"Origin": "http://foreign.invalid", "Content-Type": "application/json"},
                body=b"{}",
            )[0]
            == 403,
            "Foreign mutation origin accepted",
        )
        require(
            request(
                url,
                "/api/desktop/setup",
                method="POST",
                headers={"Origin": url.rstrip("/"), "Content-Type": "application/json"},
                body=b"{}",
            )[0]
            in {401, 404},
            "Anonymous account setup route exists",
        )
        subprocess.run(
            [str(node), str(ROOT / "tools/native_feature_smoke.mjs"), url, str(output)],
            cwd=ROOT,
            env={
                **os.environ,
                "NATIVE_TEST_PASSWORD": password,
                "NATIVE_TEST_COOKIE_NAME": expected_cookie,
            },
            check=True,
            timeout=80,
        )
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.stdin.close()
        actual_exit = process.wait(timeout=20)
        reader.join(timeout=3)
        require(
            actual_exit == 0 and not reader.is_alive(),
            "Native owner Quit did not close its process/output pipe",
        )
        target = urlsplit(url)
        try:
            connection = socket.create_connection(("127.0.0.1", target.port), timeout=1)
        except OSError:
            pass
        else:
            connection.close()
            raise ValueError("Owned service remains reachable after Quit")
        reopened = Profile(profile_directory)
        try:
            require(
                reopened.count_users() == len(ROLES),
                "Saved profile accounts changed or owner lock remains held",
            )
        finally:
            reopened.close()
        require(
            all(password not in line for line in log), "Test password leaked into process output"
        )
        passed = True
    finally:
        if process.poll() is None:
            try:
                process.stdin.write("quit\n")
                process.stdin.flush()
                process.wait(timeout=20)
            except (OSError, ValueError, subprocess.TimeoutExpired):
                forced = True
                process.kill()
                process.wait(timeout=10)
        reader.join(timeout=3)
        (output / "service.log").write_text("".join(log))
        (output / "native.json").write_text(
            json.dumps(
                {
                    "package": expected,
                    "passed": passed,
                    "forced_cleanup": forced,
                    "actual_application_exit": actual_exit,
                    "actual_frozen_tk_diagnostic": True,
                    "source_server_fallback": False,
                    "no_developer_runtime_path": True,
                    "synthetic_profile_only": True,
                },
                indent=2,
            )
            + "\n"
        )
    require(passed and not forced, "Native acceptance did not pass cleanly")
    print("Actual extracted application, real private-role workflow and owner Quit passed")


if __name__ == "__main__":
    main()
