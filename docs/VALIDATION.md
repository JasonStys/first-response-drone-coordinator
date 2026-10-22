# Validation record

By Jason Stys. Synthetic exercise evidence only. Local Windows verification and source-linked GitHub matrix results are recorded separately; pending checks are not labelled passed.

## Local baseline — 2026-10-21

- Windows / Python 3.14.6 / Node 24.18.1, npm 11.16.0.
- Backend: 68 tests passed; branch-aware coverage 98.14%; planner, scenario contracts, examples and persistence at 100% in that run.
- TypeScript helpers: 21 tests passed, 100% statements/branches/functions/lines in the declared pure-helper denominator.
- Strict TypeScript and production Vite build passed; npm and hash-locked Python dependency audits reported no known vulnerabilities at scan time.
- Initial browser run: 9/12 passed; three failures shared one harness assumption: `.check()` expected an immediate controlled-checkbox change, while the UI intentionally waits for server acknowledgement. Acceptance now clicks the control and separately awaits both its checked state and the actual saved revision message. The server/state assertions remain required.
- First test invocation lacked the parent `.runtime` folder for a custom pytest base directory. Creating that test-output parent fixed the environment setup; production initialization already creates its database directory.
- A cookie assertion used an unsupported private httpx attribute. It was corrected to inspect the public cookie jar and require the HttpOnly attribute, not bypass the assertion.
- The next browser attempt exposed an ambiguous locator matching both the global stand-down banner and four per-task reasons. It was scoped to the actual global banner; task/result assertions were retained. Final local run: **12/12 passed** across Chromium, Firefox and WebKit, with zero retries, including non-default alternative review, stale invalidation, actual JSON download, injection-safe rendering, offline refresh gate, accessibility, mobile and keyboard checks.
- Strict unused-symbol TypeScript checks, Ruff lint/format, generated source indexes and all-file/header/Action-pin contracts passed. Local production gzip: JS 73,420 B / 100,000 B budget; CSS 2,068 B / 12,000 B budget.
- Three-run median search timings: wildfire 34.540 ms; flood 31.706 ms; search 35.134 ms; restoration 37.928 ms. Each fully enumerated 2,789 states. Maximum-size fixture: 1,210.838 ms median, 25,000 states, `truncated=true`, `optimal=false`; three independently revalidated feasible alternatives. Timing is an observation, not an operational SLO.
- CLI help and non-overwriting initialization were exercised against a separate synthetic database. Browser acceptance launches the same application factory and real SQL store. Starlette emits a known httpx TestClient deprecation warning; it is visible and not counted as a failed test or silently suppressed.

## Hosted acceptance — source baseline `9b03261d0294d9f003be33f80b20bd035da4d4bd`

[Validation run 39710960594](https://github.com/JasonStys/first-response-drone-coordinator/actions/runs/39710960594) tests the actual source baseline, with no mocked service routes:

- Ubuntu 24.04 / Python 3.12: passed, 68 backend cases and 21 helper cases, lint/format/index contracts, production build, payload budget and deterministic benchmark.
- Windows / Python 3.14: passed the same full core suite; branch-aware coverage 97.96% (frontend assets are not built yet during core API tests).
- macOS / Python 3.14: passed the full core suite.
- Ubuntu 24.04 / Python 3.14: passed the full core suite, benchmark, Python dependency audit and final npm audit. **The overall Validation run completed successfully with all five jobs green.**
- Actual-service browser job on Ubuntu: **12/12 passed**, Chromium/Firefox/WebKit, zero retries, 24.3 seconds test duration.

[CodeQL run 39710960443](https://github.com/JasonStys/first-response-drone-coordinator/actions/runs/39710960443) passed both Python and JavaScript/TypeScript security-and-quality jobs. Open code-scanning alerts were separately queried after analysis: **zero**. No source change, audit bypass or reduced threshold was required for the observed npm registry delays; completed install steps reported zero vulnerabilities.

The documentation/evidence update repeats the unchanged full gates on its own head commit. Current status remains visible in the [Validation workflow](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/validate.yml) and [CodeQL workflow](https://github.com/JasonStys/first-response-drone-coordinator/actions/workflows/codeql.yml); these links expose exact source identity rather than suggesting this dated snapshot proves arbitrary future commits.

## Actions storage

Before any new workflow was triggered: 97 owned repositories, 62,959,952 bytes of Actions artifacts (~63.0 MB decimal); 8,185,324,614 bytes of separate caches (~8.19 GB). GitHub quota percentage unavailable; private-repository artifact bytes zero. Fresh check at 2026-10-21 19:24:59 PDT: 98 repositories and those same byte counts. The new repository has zero Actions artifacts. No runs, artifacts or caches were deleted. Workflows intentionally upload neither artifacts nor Actions caches.

## Limits

These results establish behavior within the documented synthetic planning model, not real emergency readiness, flight feasibility, legal permission, physical safety, security certification or a production availability guarantee. No public deployment or installer is represented as tested.
