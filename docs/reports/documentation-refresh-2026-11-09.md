# Documentation refresh — 2026-11-09

By Jason Stys.

This documentation-only edition describes source `26aa28b2fe772506d1dfcc0a388a1bea94802897`. It does not change application behavior, accounts, private data, installers or published releases.

## Published editions and completed review

| File | Bytes | SHA-256 | Reviewed scope |
| --- | ---: | --- | --- |
| [project-guide.docx](project-guide.docx) | 46744 | `f1dc800b8d1270c31aa326911882d67d9d347de1348eb5d38e1ba4c38233d084` | 6 pages, each viewed individually |

Word review checked plain black titles, readable pagination, whole table rows, source references, practical limits and absence of clipping or overflow. Render receipts were matched to the current DOCX digest before approval.

## Evidence and change boundary

- Functional baseline: `26aa28b2fe772506d1dfcc0a388a1bea94802897`.
- Workflow observation: `2026-11-10T05:25:40.628667+00:00`; exact run URLs and source identities remain in [publications.json](publications.json).
- Local document-package validation verifies exact copied bytes, Office ZIP integrity, approved page/tab identities and internal documentation links. Repository-specific documentation and source-policy commands are run separately and recorded in the integration handoff.
- Source/index metadata is regenerated using the repository’s existing tools. Existing privacy, security, coverage and workflow gates are retained.
- PR and later main workflows must pass independently. This record does not claim future or unrun integration CI success.

## Interpretation

The Word files document the cited source; dated source reports retain their original execution scope. A passing workflow is distinct from completed analysis with zero findings, and neither establishes production suitability. Checksums identify exact bytes, not a signature or publisher attestation.

Use the [handbook](../handbook.md) to choose usage, design, security and test documentation. Keep editable Markdown and reviewed editions together; do not replace historical measurements with undated claims.

## Integration-local checks

Observed at `2026-11-10T08:08:12.981755+00:00` on Windows with this repository’s existing development tools. Python commands use its isolated development environment. The documentation source baseline remains the immutable revision above; these checks validate this documentation integration locally.

| Command | Observed result |
| --- | --- |
| `python tools/docs_index.py` | Passed, exit 0. |
| `python tools/docs_index.py --check` | Passed, exit 0. |
| `python -m ruff check coordinator tests tools` | Passed, exit 0. |
| `python -m ruff format --check coordinator tests tools` | Passed, exit 0. |
| `python -m pytest --cov=coordinator --cov-report=term-missing` | Passed, exit 0. |
| `node node_modules/vitest/vitest.mjs run --coverage` | Passed, exit 0. |
| `node node_modules/typescript/bin/tsc --noEmit` | Passed, exit 0. |
| `python tools/check_repo.py` | Passed, exit 0. |

The independent publication audit also matched every copied Office file to its approved SHA-256, checked ZIP package integrity and current page/tab approvals, compared immutable workflow/source metadata, and resolved every local handbook/report link within the repository. Hosted PR/main, browser, platform and container jobs remain separate required checks; they are not inferred from these local results.



The complete unchanged Python and coverage-gated TypeScript suites, strict compilation and source policy passed. The initial restricted sandbox attempt timed out while denied test-owned loopback access; the unchanged suites completed with narrowly scoped execution access. Only the exact reviewed project-guide.docx path receives Office handling: both navigation and the existing hygiene scan inspect its ZIP XML text rather than broadly excluding binary extensions. Unknown files retain their previous checks. No aircraft, live airspace provider or user account was accessed.

## Publication-reader review

Independent review identified two limits in the first documentation reader: ZIP/XML expansion was not bounded, and relationship parts were not inspected by the original hygiene scan. The exact reviewed Word path now uses a maximum of 256 unique members, 8 MiB total expanded bytes and 2 MiB XML/relationship text. Required Word parts, duplicate members, VBA and embedded objects are rejected; ZIP CRC integrity is checked before text inspection. Both `.xml` and `.rels` content pass through the unchanged original credential patterns. Unknown binary filenames remain strict UTF-8 failures.

Ten independent real-ZIP regression tests verify readable XML and relationships; actual main-checker rejection of a credential in either part; exact-filename handling; and malformed, macro, embedded, oversized and duplicate packages. The complete local Python suite passed 119 tests with the unchanged 90% runtime coverage floor, together with coverage-gated TypeScript tests, strict compilation, both current catalog modes, lint, formatting and the original source hygiene gate. The reader is a source-publication checker, not a general-purpose untrusted document import service. Later hosted checks remain separate required evidence.
