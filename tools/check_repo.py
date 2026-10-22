"""Jason Stys: public-source, header, workflow-pin and gzip payload budget gates.

Functions and variable lines: docs/SOURCE_MAP.md. Narrow credential patterns do not
constitute a comprehensive secret scan or an independent security certification.
"""

import gzip
import re
import sys

from docs_index import ROOT, files


def main():
    """Fail missing author/source headers, mutable Action pins, known token patterns or oversize UI."""
    for path in files():
        content = path.read_text(encoding="utf-8")
        assert not re.search(
            r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----",
            content,
        ), path
        if path.suffix in (".py", ".ts", ".tsx", ".css", ".html", ".mjs", ".sql"):
            header = "\n".join(content.splitlines()[:12])
            assert "Jason Stys:" in header, path
            assert "SOURCE_MAP.md" in header or "FILE_CATALOG.md" in header, path
        if path.parent.name == "workflows":
            assert "upload-artifact" not in content and "actions/cache" not in content
            for action in re.findall(r"uses:\s*([^\s]+)", content):
                assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", action), action
    if "--dist" in sys.argv:
        scripts = list((ROOT / "dist/assets").glob("*.js"))
        styles = list((ROOT / "dist/assets").glob("*.css"))
        assert scripts and styles and (ROOT / "dist/index.html").is_file()
        js, css = (
            sum(len(gzip.compress(path.read_bytes())) for path in paths)
            for paths in (scripts, styles)
        )
        assert js <= 100000 and css <= 12000, (js, css)
        print(f"Production gzip: JS {js} B / 100000; CSS {css} B / 12000")
    print("Public source, headers and immutable Actions checks passed")


if __name__ == "__main__":
    main()
