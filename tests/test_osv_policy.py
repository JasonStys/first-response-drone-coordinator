"""Jason Stys: independently enforce OSV inventory completeness and no-suppression result policy.

Tests/variables/line locations: docs/SOURCE_MAP.md. Fixtures test report policy only;
the required hosted job runs the checksum-verified official scanner against live OSV.
"""

import pytest

from tools.audit_osv import expected_packages, verify_report


def lock():
    """Minimal resolved lock including a nested version and optional-platform identity."""
    return {
        "lockfileVersion": 3,
        "packages": {
            "": {"name": "root"},
            "node_modules/a": {"version": "1.0"},
            "node_modules/a/node_modules/@scope/b": {"version": "2.0", "optional": True},
        },
    }


def report():
    """Complete clean scan fixture, never used instead of the live scanner in CI."""
    return {
        "results": [
            {
                "source": {"type": "lockfile", "path": "/synthetic/package-lock.json"},
                "packages": [
                    {"package": {"name": name, "version": version, "ecosystem": "npm"}}
                    for name, version in expected_packages(lock())
                ],
            }
        ]
    }


def test_complete_inventory():
    """Nested names and optional dependencies must all appear in the scanned inventory."""
    expected = expected_packages(lock())
    assert expected == {("a", "1.0"), ("@scope/b", "2.0")}
    assert verify_report(report(), expected) == 2


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data.update(lockfileVersion=1),
        lambda data: data.update(packages={}),
        lambda data: data["packages"]["node_modules/a"].pop("version"),
        lambda data: data["packages"]["node_modules/a"].update(link=True),
    ],
)
def test_invalid_lock(change):
    """No unresolved, empty or linked dependency can silently disappear from coverage."""
    data = lock()
    change(data)
    with pytest.raises(ValueError):
        expected_packages(data)


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data.update(errors=["provider unavailable"]),
        lambda data: data.update(results=[]),
        lambda data: data["results"][0]["source"].update(path="other.json"),
        lambda data: data["results"][0]["source"].update(type="directory"),
        lambda data: data["results"][0].update(packages=None),
        lambda data: data["results"][0]["packages"].pop(),
        lambda data: data["results"][0]["packages"][0]["package"].update(ecosystem="Go"),
        lambda data: data["results"][0]["packages"][0].update(
            vulnerabilities=[{"id": "synthetic-test-finding"}]
        ),
        lambda data: data["results"][0]["packages"][0].update(vulnerabilities=None),
        lambda data: data["results"][0]["packages"][0].update(
            groups=[{"ids": ["synthetic-test-finding"]}]
        ),
    ],
)
def test_incomplete_or_finding_never_passes(change):
    """Scanner errors, missing packages, any-severity findings and malformed results fail closed."""
    data = report()
    change(data)
    with pytest.raises(ValueError):
        verify_report(data, expected_packages(lock()))
