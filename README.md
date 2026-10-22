# First Response Drone Coordinator

[![Validation](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/validate.yml/badge.svg)](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/validate.yml)
[![CodeQL](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/codeql.yml/badge.svg)](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/codeql.yml)

A human-supervised **resource-planning exercise application** for first-response drone teams, by [Jason Stys](https://github.com/JasonStys) ([contact](https://www.linkedin.com/in/jason-stys-31b30b351/)).

An incident team may have more observation requests than available qualified operators, sensor-equipped aircraft, time and nominal battery capacity. This application makes those trade-offs inspectable: prepare a synthetic incident, compare allocations, explain coverage gaps, and have a different reviewer record a planning judgement. A changed condition invalidates the old review instead of silently reusing it.

**Not an emergency-response system, flight planner, dispatch service, FAA authorization tool, or air-traffic feed.** All templates use fictional people, cells and equipment values. No real aircraft, radios, coordinates, surveillance feeds or model APIs are connected. Never use the output to conduct a flight or direct an actual emergency response.

## What it demonstrates

| Feature | What works | Important boundary |
| --- | --- | --- |
| Resource allocation | Up to three deterministic alternatives; priority coverage, task count, then earlier starts | Search limit is explicit; incomplete searches never claim optimality |
| Conflict assurance | Independent validation of aircraft, operator and cell overlap; qualifications, availability, time windows and cumulative battery reserves | Five-minute abstract slots; no travel, terrain, recharge or physical flight model |
| Human oversight | Separate planner/reviewer/observer accounts; independent review, notes, revision invalidation and history | Review is not legal authorization or a launch command |
| Stop gates | Communications loss, crewed aircraft activity and weather hold prevent allocations | Conditions are manually entered, not sensed or verified |
| Flexible exercises | Wildfire perimeter, flood assessment, area-search planning and infrastructure restoration; bounded JSON editor | Synthetic-only contract; no real personal information or automatic person detection |
| Evidence | Authenticated JSON export with scenario, alternatives, gaps, recorded review, stale flags and audit window | Planning debrief, not proof a flight or rescue occurred; latest 20 proposals/100 audit events |
| Browser experience | Responsive fictional coverage grid, resource cards, task allocations, help, keyboard access and author links | No offline write queue; reconnect requires refresh |
| Local privacy | Argon2id passwords, opaque sessions, role checks, CSRF/origin/Host checks, restrictive CSP | One trusted workspace; host/database administrators can access stored data |

TypeScript/React handles typed browser interactions; Python handles strict input validation, bounded combinatorial search and HTTP orchestration; SQL handles transactional persistent state. No language is included merely to inflate the language count. There is no LLM in the decision path: constraints and objectives are deterministic and explainable.

## Quick start: disposable local demo

Prerequisites: Python 3.12–3.14, Node 24, npm, Git. Dependency downloads require internet; normal runtime does not. Commands below work from this repository in PowerShell; on macOS/Linux replace `.venv/Scripts/python` with `.venv/bin/python`.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install --require-hashes -r requirements-dev.lock
npm ci --ignore-scripts --no-audit
npm run build
.venv/Scripts/python tools/serve_demo.py
```

Open <http://127.0.0.1:8861/>. Demo usernames: `planner`, `reviewer`, `observer`. Their **public synthetic demo-only** password is `Synthetic-demo-only-2026!`. These accounts are created only by the explicitly launched disposable demo helper, in a new temporary database removed on graceful shutdown. Never reuse that password, expose the demo to a network, or put private information into it.

1. Sign in as `planner`, inspect conditions and resources, then **Generate alternatives**.
2. Inspect coverage gaps. The fourth template task deliberately lacks a recorded authorization.
3. Sign out and sign in as `reviewer`. Compare options, acknowledge limits, add a note and record the planning review.
4. Sign in as `planner` and change crewed-aircraft activity. The old review becomes stale; a fresh proposal has no allocations.
5. Export the exercise evidence. Help and safety limits are available inside the interface.

## Persistent local workspace: no built-in accounts

```powershell
.venv/Scripts/python -m coordinator init --scenario flood
.venv/Scripts/python -m coordinator user alice --role planner
.venv/Scripts/python -m coordinator user bob --role reviewer
.venv/Scripts/python -m coordinator user reader --role observer
.venv/Scripts/python -m coordinator serve
```

Passwords are prompted privately, not passed on the command line. Initialization does not overwrite existing data. The private SQLite database lives in ignored `.runtime/workspace.db`. To choose another database, place `--db PATH` **before** the subcommand. The CLI binds only to loopback. This is a source-distributed local browser application, not a signed installer, public SaaS deployment, PWA or native mobile app.

## Verification

```powershell
.venv/Scripts/python -m ruff check coordinator tests tools
.venv/Scripts/python -m ruff format --check coordinator tests tools
.venv/Scripts/python -m pytest --cov=coordinator --cov-report=term-missing
npm run format:check
npm test
npm run build
.venv/Scripts/python tools/docs_index.py --check
.venv/Scripts/python tools/check_repo.py --dist
.venv/Scripts/python -m pip_audit --disable-pip --no-deps -r requirements-dev.lock
npm run audit
# Install matching browser binaries once:
npx playwright install chromium firefox webkit
$env:COORD_PYTHON = (Resolve-Path .venv/Scripts/python.exe).Path
npm run test:e2e
.venv/Scripts/python tools/benchmark.py
```

On POSIX use `COORD_PYTHON="$PWD/.venv/bin/python" npm run test:e2e`. CI also installs Linux browser system dependencies. `npm run audit` uses a strict full-lockfile audit with bounded retries for transient registry outages; a missing/incomplete audit fails closed. Install-time `--no-audit` avoids redundant incidental requests; the dedicated required audit still runs. CI uses Windows for that platform-independent lockfile gate and Linux for Python dependency auditing. Coverage gates: backend ≥90% branch-aware over `coordinator/` excluding only the interactive CLI; TypeScript pure helper statements/functions/lines ≥95%, branches ≥90%. Browser coverage is behavioral, not a claim that all UI branches have instrumentation coverage. See [measured validation](docs/VALIDATION.md), [test design](docs/TESTING.md) and [Actions](https://github.com/JasonStys/first-response-drone-coordinator/actions).

## Code and file navigation

| Area | Responsibility |
| --- | --- |
| `coordinator/models.py` | Strict bounded scenario, allocation and API request schemas |
| `coordinator/planner.py` | Eligibility, independent plan validation, objective and bounded alternatives search |
| `coordinator/examples.py` | Four synthetic scenario factories |
| `coordinator/schema.sql`, `store.py` | Private tables, atomic revision writes, proposals, review and audit history |
| `coordinator/auth.py`, `api.py` | Account/session/role boundary, same-origin API and fixed static frontend |
| `coordinator/__main__.py` | Local initialization, interactive user provisioning and serving |
| `ui/src/main.tsx`, `domain.ts`, `style.css` | Actual-service browser workspace, typed pure helpers and responsive design |
| `tests/` | Independent exhaustive oracle, security/API/concurrency tests and three-engine acceptance |
| `tools/` | Disposable demo, measured benchmark and source/documentation contract checks |
| `.github/workflows/` | Four OS/Python core combinations, browser acceptance, dependency audits and CodeQL |
| `docs/` | Architecture decisions, primary research, operations/help, threat model, test plan and validation evidence |

Every file has a specific responsibility in the generated [complete file catalog](docs/FILE_CATALOG.md). Source headers link to the generated [exact function/class/parameter/variable line index](docs/SOURCE_MAP.md); CI rejects stale indexes. This avoids handwritten line numbers drifting after edits.

## Limits and extension points

The solver supports six indivisible tasks, four aircraft, four operators and twelve five-minute slots, with a 25,000-node default cap. Task priority is an exercise input, not an automated judgement about human worth or urgency. Nominal battery budgets do not predict safe endurance; task separation by cell does not prove collision avoidance. Adding real geospatial, authorization, aircraft or emergency data would require a separate design, privacy assessment, operational validation and qualified domain review.

SQLite and one local workspace intentionally replace a PostgreSQL/PostGIS deployment: this version needs neither real coordinates nor distributed operation. No PostgreSQL, cloud failover, tenant isolation, native installer, compliance certification or emergency readiness is claimed.

Original code developed with AI assistance and verified through reproducible automated and manual checks; not independently audited. See [architecture](docs/ARCHITECTURE.md), [operations](docs/OPERATIONS.md), [security](docs/SECURITY.md), [research](docs/RESEARCH.md) and [contributing](CONTRIBUTING.md). MIT license; dependency licenses remain independent.
