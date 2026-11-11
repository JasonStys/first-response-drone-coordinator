"""Jason Stys: inspect the exact current Word XML and retain unknown-binary refusal. Functions and variables: docs/SOURCE_MAP.md."""

from zipfile import ZipFile

import pytest

from tools import docs_index as policy


def test_current_edition_exposes_document_and_relationships(tmp_path, monkeypatch):
    """A genuine named ZIP is searchable; a renamed unknown binary does not become a publication exception."""
    if hasattr(policy, "ROOT"):
        monkeypatch.setattr(policy, "ROOT", tmp_path)
    current = tmp_path / "docs/reports/windows-application-guide-0.2.1.docx"
    current.parent.mkdir(parents=True)
    with ZipFile(current, "x") as package:
        package.writestr("[Content_Types].xml", "<Types/>")
        package.writestr(
            "word/document.xml", "<document>current-installed-review-marker</document>"
        )
        package.writestr(
            "word/_rels/document.xml.rels",
            '<Relationships><Relationship Target="https://github.com/JasonStys"/></Relationships>',
        )
    content = policy.public_text(current)
    assert "current-installed-review-marker" in content
    assert "github.com/JasonStys" in content
    unknown = current.with_name("unknown-current.docx")
    unknown.write_bytes(b"\xffinert-unknown-binary")
    with pytest.raises(UnicodeDecodeError):
        policy.public_text(unknown)
