"""Jason Stys: generate/check exact declaration lines and all-file responsibility catalog.

Functions/variables and lines: docs/SOURCE_MAP.md. Does not execute indexed source.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {
    ".git",
    ".venv",
    ".runtime",
    "node_modules",
    "dist",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "test-results",
    "playwright-report",
}
DESCRIPTIONS = {
    ".gitattributes": "Portable text normalization and explicit reviewed Word binary handling.",
    "docs/handbook.md": "Organized current usage, architecture, security and validation entry point.",
    "docs/reports/project-guide.docx": "Reviewed Word guide bound to the documented source revision.",
    "docs/reports/publications.json": "Exact publication digests, approved page identities and immutable source baseline.",
    "docs/reports/documentation-refresh-2026-11-09.md": "Dated documentation integration validation and interpretation limits.",
    "README.md": "Purpose, feature summary, reproducible setup, use cases, scope and file navigation.",
    "LICENSE": "MIT license for original source; dependencies retain their own licenses.",
    "CONTRIBUTING.md": "Contributor workflow, test gates and review expectations.",
    "SECURITY.md": "Private vulnerability disclosure instructions and supported local trust boundary.",
    "requirements.in": "Direct production Python dependency pins.",
    "requirements.lock": "Production transitive dependency versions and SHA256 integrity hashes.",
    "requirements-dev.in": "Production plus direct test, style and audit tool pins.",
    "requirements-dev.lock": "Cross-platform development dependency hash lock, including production requirements.",
    "package.json": "Exact frontend dependencies, scripts, Node support and license metadata.",
    "package-lock.json": "npm resolved versions and integrity hashes.",
    "pyproject.toml": "Python support, strict linting, test settings and 90% branch-aware coverage gate.",
    "tsconfig.json": "Strict TypeScript compilation for UI, helpers, browser tests and build config.",
    "docs/ARCHITECTURE.md": "Requirements, data flow, architecture decisions, optimizer constraints and complexity.",
    "docs/OPERATIONS.md": "Local account setup, demo walkthrough, backups, recovery and troubleshooting.",
    "docs/SECURITY.md": "Threat model, tested protections, data ownership and remaining risks.",
    "docs/TESTING.md": "Independent oracle, constraint tests, browser gates and coverage denominators.",
    "docs/VALIDATION.md": "Measured results, corrections, source-linked Actions evidence and storage observations.",
    "docs/RESEARCH.md": "Primary FAA, SQLite, OWASP and tool references with design consequences.",
    "docs/SOURCE_MAP.md": "Generated exact declaration, parameter and assigned variable physical line index.",
    "docs/FILE_CATALOG.md": "Generated responsibility summary for every tracked deliverable.",
}


def public_text(path: Path) -> str:
    """Inspect all XML/relationships in the one authored Word path; unknown binary files still fail closed."""
    if path.relative_to(ROOT).as_posix() != "docs/reports/project-guide.docx":
        return path.read_text(encoding="utf-8")
    with ZipFile(path) as package:
        members = package.infolist()
        names = [member.filename for member in members]
        if (
            len(members) > 256
            or len(set(names)) != len(names)
            or sum(member.file_size for member in members) > 8 * 1024 * 1024
            or "word/document.xml" not in names
            or "[Content_Types].xml" not in names
            or any("vbaProject" in item or item.startswith("word/embeddings/") for item in names)
        ):
            raise ValueError("Invalid or unsupported reviewed Word package")
        inspected = [member for member in members if member.filename.endswith((".xml", ".rels"))]
        if sum(member.file_size for member in inspected) > 2 * 1024 * 1024:
            raise ValueError("Reviewed Word XML exceeds inspection budget")
        if package.testzip() is not None:
            raise ValueError("Reviewed Word package integrity failed")
        return "\n".join(package.read(member).decode("utf-8") for member in inspected)


def files():
    """Enumerate authored text only, avoiding private databases, build and dependency directories."""
    paths = []
    for directory, subdirectories, names in os.walk(ROOT):
        subdirectories[:] = [name for name in subdirectories if name not in EXCLUDE]
        paths.extend(Path(directory) / name for name in names if not name.startswith(".coverage"))
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def render():
    """Use Python/TypeScript ASTs to avoid fragile hand-maintained physical line numbers."""
    catalog = [
        "# File catalog",
        "",
        "By Jason Stys. Generated by `python tools/docs_index.py`.",
        "",
        "| File | Responsibility |",
        "| --- | --- |",
    ]
    source = [
        "# Source declaration map",
        "",
        "By Jason Stys. Headers link here for exact current physical line locations.",
        "Python AST indexes functions/classes, arguments and assigned names; TypeScript AST indexes declarations, parameters and binding names.",
        "Function/class docstrings describe responsibility; this is navigation, not dead-code or call-graph analysis.",
        "",
        "| File | Line | Declaration / variable |",
        "| --- | ---: | --- |",
    ]
    for path in files():
        relative = path.relative_to(ROOT).as_posix()
        text = public_text(path)
        description = DESCRIPTIONS.get(relative) or next(
            (line.strip(' #/*!-"<>') for line in text.splitlines()[:12] if "Jason Stys:" in line),
            None,
        )
        if description is None:
            raise ValueError(f"Add a meaningful file description: {relative}")
        catalog.append(f"| `{relative}` | {description.replace('|', '/')} |")
        if path.suffix == ".py":
            records = []
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    params = (
                        "class"
                        if isinstance(node, ast.ClassDef)
                        else ", ".join(arg.arg for arg in node.args.args)
                    )
                    records.append((node.lineno, f"{node.name}({params})"))
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    records.append((node.lineno, node.id))
            source.extend(
                f"| `{relative}` | {line} | `{name}` |" for line, name in sorted(set(records))
            )
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js required to index TypeScript declarations")
    source.extend(
        subprocess.check_output([node, "tools/source_index.mjs"], cwd=ROOT, text=True, timeout=30)
        .strip()
        .splitlines()
    )
    return {
        "docs/FILE_CATALOG.md": "\n".join(catalog) + "\n",
        "docs/SOURCE_MAP.md": "\n".join(source) + "\n",
    }


def main():
    """Generate or fail on stale checked-in navigation; never silently rewrite during CI."""
    for name, content in render().items():
        path = ROOT / name
        if "--check" in sys.argv:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale {name}: run python tools/docs_index.py")
        else:
            path.write_text(content, encoding="utf-8")
    print(f"Source/file indexes verified for {len(files())} files")


if __name__ == "__main__":
    main()
