"""Jason Stys: audit retry/failure policy unit tests, not substitutes for actual live audits.

Functions/fixtures/variable locations: docs/SOURCE_MAP.md. Injected subprocess results
exercise error classification only; CI's dedicated audit still queries real npm data.
"""

import json
import subprocess

import pytest

from tools.audit_npm import assess, audit


def clean():
    """Construct the npm v2 empty-findings contract for policy-only unit tests."""
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {},
        "metadata": {
            "vulnerabilities": {
                "info": 0,
                "low": 0,
                "moderate": 0,
                "high": 0,
                "critical": 0,
                "total": 0,
            }
        },
    }


@pytest.mark.parametrize(
    "report,code,expected",
    [
        (clean(), 0, "passed"),
        (clean(), 1, "failed"),
        ({}, 0, "failed"),
        ([], 0, "failed"),
        ({"metadata": None}, 0, "failed"),
        ({"metadata": {"vulnerabilities": []}}, 0, "failed"),
        ({"error": {"code": "E503"}}, 1, "retry"),
        ({"error": {"summary": "503 Service Unavailable - POST registry"}}, 1, "retry"),
        ({"error": {"code": "E401"}}, 1, "failed"),
        ({"error": {"code": []}}, 1, "failed"),
        (
            {
                "error": {},
                "message": "network timeout at: https://registry.npmjs.org/-/npm/v1/security/advisories/bulk",
            },
            1,
            "retry",
        ),
        ({"error": {}, "message": "unexpected authentication failure"}, 1, "failed"),
    ],
)
def test_classification(report, code, expected):
    """No zero-exit empty report, permanent error or unknown response can pass."""
    assert assess(report, code) == expected


@pytest.mark.parametrize("level", ["high", "critical"])
def test_findings_never_retry(level):
    """High/critical findings fail even with a simultaneous transient code or zero exit."""
    report = clean()
    report["metadata"]["vulnerabilities"][level] = 1
    report["metadata"]["vulnerabilities"]["total"] = 1
    report["error"] = {"code": "E503"}
    assert assess(report, 0) == "failed"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda report: report.update(auditReportVersion=1),
        lambda report: report["metadata"]["vulnerabilities"].update(high=False),
        lambda report: report["metadata"]["vulnerabilities"].update(total=2),
    ],
)
def test_malformed_complete_report(mutation):
    """Wrong version, coerced booleans and inconsistent totals fail closed."""
    report = clean()
    mutation(report)
    assert assess(report, 0) == "failed"


def test_transient_then_actual_report_contract():
    """Exercise bounded backoff while retaining the full unchanged audit command."""
    responses = [
        subprocess.CompletedProcess([], 1, json.dumps({"error": {"code": "E503"}})),
        subprocess.CompletedProcess([], 0, json.dumps(clean())),
    ]
    calls, sleeps = [], []

    def run(command, **kwargs):
        """Capture policy invocation; this is not used by the actual CLI audit."""
        calls.append((command, kwargs))
        return responses.pop(0)

    assert audit(run, sleeps.append, "npm-test-only") == 0
    assert sleeps == [2] and len(calls) == 2
    assert "--audit-level=high" in calls[0][0]
    assert "--package-lock-only" in calls[0][0]
    assert "--include=dev" in calls[0][0] and "--include=optional" in calls[0][0]
    assert not any("omit" in item or "force" in item for item in calls[0][0])
    assert calls[0][1]["timeout"] == 90


@pytest.mark.parametrize("kind,expected_calls", [("timeout", 3), ("malformed", 1), ("oserror", 1)])
def test_unavailable_never_passes(kind, expected_calls):
    """Exhausted timeouts, bad JSON and launch errors cannot fabricate a clean audit."""
    calls = []

    def run(command, **kwargs):
        """Inject deterministic failure without contacting a provider or bypassing real CI."""
        calls.append(command)
        if kind == "timeout":
            raise subprocess.TimeoutExpired(command, 90)
        if kind == "oserror":
            raise OSError("not executable")
        return subprocess.CompletedProcess([], 0, "not JSON")

    assert audit(run, lambda _: None, "npm-test-only") == 1
    assert len(calls) == expected_calls


def test_missing_npm(monkeypatch):
    """Absent tooling is an unavailable audit, never a skipped security success."""
    monkeypatch.setattr("tools.audit_npm.shutil.which", lambda _: None)
    assert audit() == 1
