"""Jason Stys: actual subprocess/JUnit failure sensitivity for the mandatory notice runner. Lines: docs/SOURCE_MAP.md."""

import pytest

from tools.notice_contract import run_contract


@pytest.mark.parametrize("fault", ["failure", "skip", "missing-case"])
def test_notice_runner_cannot_turn_child_fault_into_a_pass(tmp_path, fault):
    """Small real pytest children exercise nonzero/skip/cardinality refusal, not a mocked return code."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/runtime_notices.py").write_text("# inert reader identity fixture\n")
    count = 12 if fault == "missing-case" else 13
    cases = "import pytest\n"
    for index in range(count):
        body = (
            "assert False, 'independent child-failure control'"
            if fault == "failure" and index == 0
            else "pytest.skip('independent skipped-case control')"
            if fault == "skip" and index == 0
            else "assert 1 + 1 == 2"
        )
        cases += f"\ndef test_control_{index}():\n    {body}\n"
    (tmp_path / "tests/runtime_notice_cases.py").write_text(cases)
    error, reason = (
        (RuntimeError, "Notice child failed")
        if fault == "failure"
        else (ValueError, "skipped or failed records")
        if fault == "skip"
        else (ValueError, "thirteen unique")
    )
    with pytest.raises(error, match=reason):
        run_contract(tmp_path)
    assert not (tmp_path / ".runtime/notices-contract.json").exists()
