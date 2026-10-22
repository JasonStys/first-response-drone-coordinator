"""Jason Stys: bounded fail-closed npm advisory gate; only transient outages are retried.

Functions/variables and lines: docs/SOURCE_MAP.md. Never fixes dependencies, omits
packages, suppresses findings, or treats malformed/unavailable reports as success.
"""

import json
import re
import shutil
import subprocess
import time

LEVELS = ("info", "low", "moderate", "high", "critical")
TRANSIENT = {"E502", "E503", "E504", "ECONNRESET", "ETIMEDOUT", "EAI_AGAIN"}


def assess(report, returncode):
    """Classify complete npm v2 reports; findings outrank simultaneous network errors."""
    if not isinstance(report, dict):
        return "failed"
    counts = (
        report.get("metadata", {}).get("vulnerabilities", {})
        if isinstance(report.get("metadata", {}), dict)
        else {}
    )
    if isinstance(counts, dict) and any(
        type(counts.get(level)) is int and counts[level] > 0 for level in ("high", "critical")
    ):
        return "failed"
    error = report.get("error")
    if isinstance(error, dict):
        if isinstance(error.get("code"), str) and error["code"] in TRANSIENT:
            return "retry"
        summary = str(error.get("summary", ""))
        if re.match(
            r"^(502 Bad Gateway|503 Service Unavailable|504 Gateway Timeout)(?:\s|$)", summary
        ):
            return "retry"
        if str(report.get("message", "")).startswith(
            "network timeout at: https://registry.npmjs.org/-/npm/v1/security/"
        ):
            return "retry"
        return "failed"
    valid_counts = isinstance(counts, dict) and all(
        type(counts.get(level)) is int and counts[level] >= 0 for level in (*LEVELS, "total")
    )
    if (
        returncode == 0
        and report.get("auditReportVersion") == 2
        and isinstance(report.get("vulnerabilities"), dict)
        and valid_counts
        and sum(counts[level] for level in LEVELS) == counts["total"]
    ):
        return "passed"
    return "failed"


def audit(runner=subprocess.run, sleeper=time.sleep, npm=None):
    """Require an actual successful complete report within three bounded attempts.

    runner/sleeper are injection points for policy unit tests only. CLI always uses
    real npm against its configured registry; Windows uses the discovered npm.CMD.
    """
    executable = npm or shutil.which("npm")
    if executable is None:
        print("npm missing: audit unavailable, failing closed")
        return 1
    command = [
        executable,
        "audit",
        "--json",
        "--audit-level=high",
        "--package-lock-only",
        "--include=prod",
        "--include=dev",
        "--include=optional",
        "--include=peer",
        "--fetch-retries=0",
        "--fetch-timeout=30000",
    ]
    for attempt in range(1, 4):
        report = None
        try:
            result = runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=90,
                check=False,
            )
            try:
                report = json.loads(result.stdout)
                state = assess(report, result.returncode)
            except json.JSONDecodeError:
                state = "failed"
        except subprocess.TimeoutExpired:
            state = "retry"
        except OSError:
            state = "failed"
        print(
            json.dumps(
                {
                    "attempt": attempt,
                    "status": state,
                    "counts": report.get("metadata", {}).get("vulnerabilities")
                    if isinstance(report, dict) and isinstance(report.get("metadata", {}), dict)
                    else None,
                }
            )
        )
        if state == "passed":
            return 0
        if state == "failed":
            if isinstance(report, dict) and isinstance(report.get("vulnerabilities"), dict):
                print(json.dumps({"findings": report["vulnerabilities"]}))
            print("Audit findings, malformed report or permanent error: failing closed")
            return 1
        if attempt < 3:
            sleeper(2**attempt)
    print("Advisory service unavailable after three attempts: failing closed")
    return 1


if __name__ == "__main__":
    raise SystemExit(audit())
