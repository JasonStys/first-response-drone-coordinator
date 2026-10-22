# Risk-based testing strategy

By Jason Stys. Tests use only synthetic, isolated data. Safety/correctness claims remain limited to the documented planning model.

| Risk | Evidence / gate |
| --- | --- |
| Plausible but wrong objective | Thirty seeded small cases compared with a separately written exhaustive oracle; oracle does not call production candidate, validation or objective functions |
| Resource/time/energy violations | Direct adversarial assignment tests and independent revalidation of solver outputs; nominal cumulative reserve and shared-cell/crew/airframe conflicts |
| Unsupported or malformed input | Strict schema cases for unknown fields, duplicate IDs, booleans-as-integers, NaN, windows, oversized horizon, invalid cells/reserves and body-size/stream limits |
| No resources or blocked incident | Empty resource/task sets, flat batteries, excluded cells, absent recorded authorization, each global stand-down condition |
| Search cap misrepresented | Explicit tiny-budget test plus maximum-size benchmark; truncation must negate optimality; deterministic alternatives and ≤25,000 production nodes |
| Stale review / race | Actual SQLite transactions; four concurrent same-revision writers yield one winner; reject proposals saved after intervening edits; reviewed plans become stale |
| Forged review | Wrong role, self-review, unknown alternative, duplicate review, modified stored assignments and current hash/revision validation |
| Account and browser attack | Anonymous/expired/revoked sessions, password hash/digest inspection, throttling, origin/Host/CSRF boundaries, SQL injection string, secure cookie flags and restrictive headers |
| Misleading interface | Actual-service Playwright journeys for login, generate/review/invalidate/export, templates, invalid JSON contract, resource outage and escaped hostile labels |
| Offline stale state | Offline disables writes; reconnect still disables writes until a successful refresh; no background queue |
| Accessibility and portability | Chromium, Firefox and WebKit; axe WCAG 2 A/AA +2.1 AA checks, 390px viewport overflow and keyboard sign-out; Windows/macOS/Linux core matrix |
| Reproducibility and dependencies | Exact npm versions/integrities, Python hash locks, audits, immutable Action refs, strict TypeScript/Ruff/format and generated docs freshness checks |
| Advisory-service outage mistaken for success | Audit-policy unit cases for complete reports, high/critical findings, HTTP 503, timeout, permanent errors, malformed/empty JSON, inconsistent counts and retry exhaustion; actual live audit remains a separate required gate |
| Frontend footprint | Production gzip JS≤100,000 B and CSS≤12,000 B; measured in logs |

## Coverage interpretation

Backend coverage includes all production `coordinator/` modules except the interactive `__main__.py` provisioning/launcher. Coverage counts statements and branches and must be at least 90%. CLI help/init/account/server is also manually exercised; no instrumentation claim is made for interactive password entry. The planner and independent validator are expected to be fully exercised, including erroneous assignments.

Vitest instrumentation covers only pure `ui/src/domain.ts`: helper statements/functions/lines≥95%, branches≥90%. React component rendering/event code is exercised by the real-service journeys, **not** included in that percentage. Frameworks, generated bundles, vendor dependencies, test tools and documentation generators are not production coverage denominators. Generated source indexes and repository contracts have dedicated non-coverage validation.

The benchmark reports three runs per exercise and maximum-size fixture with timing, node count and truncation status. Timings are environment-dependent observations, not a real-time guarantee. Node/output bounds, reproducibility and feasibility are hard assertions. Maximum list sizes do not imply practical real-world mission coverage.

## Known limits

No actual drones, native flight simulators, airspace services, legal authorization validation, environmental prediction, rescue/detection outcomes, flight hardware or production cloud deployment is tested or claimed. No fuzz campaign, formal proof, human accessibility audit, independent penetration test or aviation certification is implied. Browser retries are zero and no route mocking is used. Historical failed validation attempts are retained rather than deleted or masked.

Run every README verification command before publishing and inspect final exact-head Actions and open CodeQL alerts. A successful workflow does not itself prove zero code-scanning findings. Unexpected failures require reproducing and fixing the implementation or test environment without weakening acceptance.

The audit helper tests inject subprocess responses solely to exercise retry/failure policy; they do not represent a real dependency scan. The CLI always executes actual npm. It requires a valid complete v2 report, consistent nonnegative severity counts, zero high/critical findings and a successful process exit. It includes production/development/optional/peer types from the full lockfile. Three attempts maximum; 30-second HTTP fetch limits, 90-second subprocess bounds and 2/4-second backoff. Unknown/permanent errors fail immediately. Hosted NPM auditing runs on Windows after observed intermittent Linux registry 503 responses; the audited lockfile is the same across the OS matrix. No findings are waived and no offline result is substituted.
