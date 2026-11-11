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
    "docs/reports/browser-host-setup-2026-11-11.md": "Observed browser setup failure, exact official CI image, real launch controls and unchanged product test boundaries.",
    "tools/check_browser_host.mjs": "Actual exact-locked browser launch/input and missing executable proof; no validation bypass.",
    "tools/check_browser_host.test.mjs": "Seven genuine child-process negatives for malformed requests and forbidden browser bypass variables.",
    "docs/reports/windows-application-guide-0.2.1.docx": "Peer-reviewed current installed application Word guide with real screenshots and immutable source.",
    "docs/reports/windows-application-guide-0.2.1.json": "Exact current document, image, source and reviewed-page identities.",
    "docs/reports/installed-windows-0.2.1-2026-11-11.md": "Observed installed and same-profile upgrade results with operating limits.",
    "docs/reports/NATIVE_CODEQL_20261111.md": "Dated actual CodeQL quality corrections, local tests and exact-source release limits.",
    "licenses/TK-9.0.5-pre-33904f039f48ed64.txt": "Verbatim archive-hash-verified prerelease Tk terms for the exact official Python3.14.10 Mac installer recipe.",
    "licenses/TCL-9.0.4.txt": "Verbatim exact official Tcl9.0.4 source notice with immutable provenance and digest-bound Mac SDK use.",
    "licenses/TK-9.0.4.txt": "Verbatim exact official Tk9.0.4 source notice with immutable provenance and digest-bound Mac SDK use.",
    "licenses/PYTHON.txt": "Official Python3.14.10 runtime license terms retained with the portable application.",
    "docs/DESKTOP.md": "Complete native profile/staff/Open/Quit workflow, actual JSON features, build steps and privacy/lifecycle limits.",
    "docs/reports/DESKTOP_CANDIDATE_20261110.md": "Dated candidate validation, original gates, real native roles/exports, observed failures and explicit release limitations.",
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
    if path.relative_to(ROOT).as_posix() not in {
        "docs/reports/project-guide.docx",
        "docs/reports/windows-application-guide-0.2.1.docx",
    }:
        return path.read_text(encoding="utf-8")
    with path.open("rb") as source:
        if os.fstat(source.fileno()).st_size > 20 * 1024 * 1024:
            raise ValueError("Reviewed Word package exceeds physical byte budget")
        with ZipFile(source) as package:
            members = package.infolist()
            names = [member.filename for member in members]
            if (
                len(members) > 256
                or len(set(names)) != len(names)
                or sum(member.file_size for member in members) > 8 * 1024 * 1024
                or "word/document.xml" not in names
                or "[Content_Types].xml" not in names
                or any(
                    "vbaProject" in item or item.startswith("word/embeddings/") for item in names
                )
            ):
                raise ValueError("Invalid or unsupported reviewed Word package")
            inspected = [
                member for member in members if member.filename.endswith((".xml", ".rels"))
            ]
            if sum(member.file_size for member in inspected) > 2 * 1024 * 1024:
                raise ValueError("Reviewed Word XML exceeds inspection budget")
            if package.testzip() is not None:
                raise ValueError("Reviewed Word package integrity failed")
            result = []
            for member in inspected:
                with package.open(member) as stream:
                    payload = stream.read(2 * 1024 * 1024 + 1)
                if len(payload) > 2 * 1024 * 1024 or len(payload) != member.file_size:
                    raise ValueError("Reviewed Word XML exceeds actual byte budget")
                result.append(payload.decode("utf-8", errors="strict"))
            return "\n".join(result)


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
