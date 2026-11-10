"""Jason Stys: independent real-ZIP publication privacy regressions. Lines: docs/SOURCE_MAP.md."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: write_document — line 49
# parameter: content — line 50
# parameter: extra — line 50
# parameter: root — line 50
# variable: path — line 53
# variable: package — line 55
# variable: name — line 59
# variable: value — line 59
# definition: test_actual_word_xml_and_relationships_remain_inspected — line 64
# parameter: monkeypatch — line 64
# parameter: tmp_path — line 64
# variable: path — line 67
# variable: result — line 70
# definition: test_actual_main_still_rejects_credentials_in_word_parts — line 76
# parameter: monkeypatch — line 77
# parameter: part — line 77
# parameter: tmp_path — line 77
# variable: token — line 80
# parameter: args — line 93
# parameter: kwargs — line 93
# definition: test_only_exact_reviewed_filename_receives_office_handling — line 99
# parameter: monkeypatch — line 99
# parameter: tmp_path — line 99
# variable: path — line 102
# variable: unknown — line 103
# variable: source — line 107
# definition: test_unsupported_or_unbounded_real_packages_fail — line 116
# parameter: defect — line 116
# parameter: monkeypatch — line 116
# parameter: tmp_path — line 116
# variable: extras — line 119
# variable: extras — line 127
# variable: i — line 127
# variable: path — line 128
# variable: package — line 130
# variable: package — line 135
# END CODE MAP

import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from tools import docs_index as policy


def write_document(root: Path, content: str, extra: dict[str, str] | None = None) -> Path:
    """Create actual small ZIP bytes independently of the production reader."""
    path = root / "docs/reports/project-guide.docx"
    path.parent.mkdir(parents=True)
    with ZipFile(path, "w") as package:
        package.writestr("[Content_Types].xml", "<Types/>")
        package.writestr("word/document.xml", content)
        package.writestr("word/_rels/document.xml.rels", "<Relationships/>")
        for name, value in (extra or {}).items():
            package.writestr(name, value)
    return path


def test_actual_word_xml_and_relationships_remain_inspected(tmp_path, monkeypatch):
    """A real ZIP yields its XML and relationship text, not a metadata placeholder."""
    monkeypatch.setattr(policy, "ROOT", tmp_path)
    path = write_document(tmp_path, "<document>Read the scoped source evidence.</document>")
    result = policy.public_text(path)
    assert "Read the scoped source evidence." in result
    assert "<Relationships/>" in result and "<Types/>" in result


@pytest.mark.parametrize("part", ["document", "relationship"])
def test_actual_main_still_rejects_credentials_in_word_parts(tmp_path, monkeypatch, part):
    """Run the genuine existing credential guard over actual ZIP XML/relationships before later gates."""
    token = "ghp_" + "A" * 32
    monkeypatch.setattr(policy, "ROOT", tmp_path)
    if part == "document":
        write_document(tmp_path, "<document>" + token + "</document>")
    else:
        write_document(
            tmp_path,
            "<document>Public.</document>",
            {"_rels/.rels": "<Relationship Target='" + token + "'/>"},
        )
    monkeypatch.setitem(sys.modules, "docs_index", policy)
    checker_path = Path(__file__).resolve().parents[1] / "tools/check_repo.py"
    spec = importlib.util.spec_from_file_location("publication_checker_fixture", checker_path)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    monkeypatch.setattr(checker, "files", lambda: [tmp_path / "docs/reports/project-guide.docx"])
    with pytest.raises(AssertionError, match="possible credential"):
        checker.main()


def test_only_exact_reviewed_filename_receives_office_handling(tmp_path, monkeypatch):
    """A renamed unknown DOCX remains rejected by strict UTF-8 handling; ordinary source stays readable."""
    monkeypatch.setattr(policy, "ROOT", tmp_path)
    path = write_document(tmp_path, "<document>Public.</document>")
    unknown = path.with_name("unreviewed.docx")
    unknown.write_bytes(path.read_bytes() + b"\xff")
    with pytest.raises(UnicodeDecodeError):
        policy.public_text(unknown)
    source = tmp_path / "source.md"
    source.write_text("Public source.", encoding="utf-8")
    assert policy.public_text(source) == "Public source."


@pytest.mark.parametrize(
    "defect",
    ["missing-main", "macro", "embedded", "xml-budget", "member-budget", "duplicate"],
)
def test_unsupported_or_unbounded_real_packages_fail(tmp_path, monkeypatch, defect):
    """Independent malformed ZIP fixtures cannot become uninspected accepted documentation."""
    monkeypatch.setattr(policy, "ROOT", tmp_path)
    extras = {}
    if defect == "macro":
        extras["word/vbaProject.bin"] = "inert test bytes"
    elif defect == "embedded":
        extras["word/embeddings/inert.bin"] = "inert test bytes"
    elif defect == "xml-budget":
        extras["word/extra.xml"] = "x" * (2 * 1024 * 1024)
    elif defect == "member-budget":
        extras = {f"word/part{i}.xml": "<x/>" for i in range(256)}
    path = write_document(tmp_path, "<document/>", extras)
    if defect == "missing-main":
        with ZipFile(path, "w") as package:
            package.writestr("[Content_Types].xml", "<Types/>")
    elif defect == "duplicate":
        with (
            pytest.warns(UserWarning, match="Duplicate name"),
            ZipFile(path, "a") as package,
        ):
            package.writestr("word/document.xml", "<document/>")
    with pytest.raises(ValueError):
        policy.public_text(path)
