# First Response Drone Coordinator handbook

By Jason Stys.

Coordinate fictional first-response mission requests, available aircraft and constrained scheduling decisions. Inspect feasibility, priorities and audit evidence without dispatching real aircraft or authorizing a flight.

Run hash-bound aircraft/operator-loss planning comparisons with planner/reviewer roles and stale-input protection.

Adds a practical civilian contingency review while preserving the saved plan and explicit resource constraints.

## Read the documentation

| Edition | Audience and contents |
| --- | --- |
| [project-guide.docx](reports/project-guide.docx) | User and developer guide: purpose, current usage, design, boundaries and source references. |

The editable Markdown remains the maintenance source. The Word files are readable editions. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [OPERATIONS](OPERATIONS.md)

### Design and contracts

- [ARCHITECTURE](ARCHITECTURE.md)
- [RESEARCH](RESEARCH.md)

### Security and validation

- [SECURITY](SECURITY.md)
- [TESTING](TESTING.md)
- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`26aa28b2fe772506d1dfcc0a388a1bea94802897`](https://github.com/JasonStys/first-response-drone-coordinator/tree/26aa28b2fe772506d1dfcc0a388a1bea94802897). The observed functional workflow baseline is `26aa28b2fe772506d1dfcc0a388a1bea94802897`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PRACTICAL_WORKFLOWS_20261109.md)
- [Current Actions](https://github.com/JasonStys/first-response-drone-coordinator/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Synthetic abstract cells, slots and resources; no actual emergency response or aircraft dispatch.
- Comparisons preserve the original objective rather than guaranteeing minimum changes to the saved plan.
- Truncated comparisons do not prove an optimum or guaranteed loss bound.
- Source-first project with current package/service validation; no public native desktop application release is supplied.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
