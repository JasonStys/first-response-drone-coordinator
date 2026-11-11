"""Jason Stys: mandatory real notice-case child with failure-sensitive bounded receipts. Lines: docs/SOURCE_MAP.md."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from defusedxml import ElementTree as ET

if not __debug__:
    raise RuntimeError("Native notice acceptance refuses optimized Python")


def run_contract(root: Path) -> dict:
    """Run the fixed owned source cases once; require all thirteen unique cases, no skips and real bytes."""
    cases = root / "tests/runtime_notice_cases.py"
    with tempfile.TemporaryDirectory(prefix="notice-contract-results-") as temporary:
        result_path = Path(temporary) / "results.xml"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(cases),
                "--capture=sys",
                "-q",
                "--junitxml=" + str(result_path),
            ],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError("Notice child failed: " + result.stdout + result.stderr)
        records = list(ET.parse(result_path).getroot().iter("testcase"))
        if len(records) != 13 or len({item.attrib["name"] for item in records}) != 13:
            raise ValueError("Expected thirteen unique actual notice cases")
        if any(list(item) for item in records):
            raise ValueError("Notice child returned skipped or failed records")
        receipt = {
            "passed": True,
            "actual_cases": [item.attrib["name"] for item in records],
            "case_count": len(records),
            "interpreter": sys.version.split()[0],
            "capture": "sys; stable native descriptors",
            "retries": 0,
            "skipped": 0,
            "case_source_sha256": hashlib.sha256(cases.read_bytes()).hexdigest(),
            "reader_source_sha256": hashlib.sha256(
                (root / "tools/runtime_notices.py").read_bytes()
            ).hexdigest(),
        }
        target = root / ".runtime/notices-contract.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
