"""Jason Stys: mandatory isolated actual Tcl notice contracts with exact-case receipt. Lines: docs/SOURCE_MAP.md."""

from pathlib import Path

from tools.notice_contract import run_contract


def test_all_thirteen_actual_notice_contracts_in_one_fresh_owned_interpreter():
    """All original real cases run once with stable descriptors; failures/skips propagate and never become absence."""
    receipt = run_contract(Path(__file__).resolve().parents[1])
    assert receipt["passed"] and receipt["case_count"] == 13
    print("All13 actual isolated Tcl/Tk notice cases passed; no retries or skips.")
