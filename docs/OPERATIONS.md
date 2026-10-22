# Local operations, help and recovery

By Jason Stys. See README for initial setup. The CLI binds `127.0.0.1` only. Do not expose the demo or service through a public tunnel.

## Choosing the mode

`python tools/serve_demo.py --port 8861` creates an isolated disposable database and three public synthetic accounts. This is for evaluation only; closing it gracefully removes the temporary database. If the process crashes, an ignored temporary folder may remain; it contains only synthetic exercise data. The persistent CLI uses `.runtime/workspace.db` and starts with **no accounts**. Initialize it and provision different named planner/reviewer accounts interactively. `init` never resets an existing scenario. Never pass passwords through arguments, source or `.env` committed to Git.

Use the active virtual environment's interpreter. On Windows `.venv/Scripts/python`; POSIX `.venv/bin/python`. If a port is occupied, choose another with `serve --port 8863` (or demo `--port`); do not stop another project's process. Browser tests reserve 8862 and refuse an existing service. Build with `npm run build` before serving; there is no separate insecure dev-server requirement.

## Workflow and help

Planner: inspect conditions and resource cards, load a template in the scenario editor, inspect JSON, and explicitly save. Loading a template alone does not change the workspace. Schema errors preserve the saved scenario. IDs must be unique within each list; task windows are earliest-inclusive/latest-exclusive. A task needs an appropriately equipped available aircraft, available qualified operator, a complete time window, a recorded external authorization review, an unexcluded fictional cell and sufficient aggregate nominal battery budget. `reserve_percent` cannot be below 20; this floor is an exercise assumption, not a manufacturer safety recommendation.

Generate alternatives. Option scores show allocated priority and task count; the final criterion prefers earlier starts. Inspect gaps and whether the search completed. Up to three distinct allocations may have identical scores; they differ in resource/time assignment. A reviewer can choose any displayed alternative, supply a note and acknowledge limits. A recorded review applies only to the option labelled **reviewed choice**. Switching the selector to another alternative is comparison, not approval transfer. The UI restores the reviewed choice on refresh.

A planner can mark an aircraft unavailable or edit qualifications, operators, windows, cells and nominal parameters through JSON. All saved changes increment revision and stale all old reviews. Checkboxes wait for server acknowledgement rather than optimistically confirming an incident hold; a pending request disables changes. Crewed-aircraft activity, weather hold or unavailable communications prevents all allocations. No review can bypass those gates.

An observer can inspect current state, history and export but cannot edit, generate or review. The UI's help panel and task table supply accessible text equivalents to the fictional grid. Author/contact links are in the footer. No map tiles, external tracking or private coordinates are loaded.

## API outline

All `/api/` reads except login require the HttpOnly session cookie. Every mutation requires `Origin` matching the configured origin and JSON content type. Authenticated writes also require `X-CSRF-Token` from login or `/api/me`.

| Endpoint | Purpose / role |
| --- | --- |
| `GET /healthz` | Anonymous liveness, no account or workspace content |
| `POST /api/login` | Bounded credentials; all roles, 20 attempts per direct address per minute |
| `GET /api/me` | Current identity, role and session CSRF token |
| `POST /api/logout` | Revoke current session, all roles |
| `GET /api/workspace`, `/api/examples` | Current snapshot/history or four synthetic templates, all roles |
| `PUT /api/workspace` | `{revision, scenario}`, planner only |
| `POST /api/proposals` | `{revision}`, planner only; returns persisted proposal ID and result |
| `POST /api/proposals/{id}/review/{alternative}` | `{revision,note,acknowledge_limits:true}`, independent reviewer only |
| `GET /api/report` | Authenticated JSON planning evidence, latest 20 proposals/100 events |

401: sign in/expired session; 403: role/CSRF/origin denial; 404: missing resource; 409: stale or already reviewed/infeasible proposal; 413: >64 KiB; 415: non-JSON; 422: invalid schema; 429: throttled sign-in; 503: uninitialized DB or missing frontend build. The service does not log credential bodies or per-request access logs through supplied launchers.

## Backup, accounts and rollback

Stop the process gracefully before backing up the complete SQLite database to a private encrypted destination. A stopped database copy avoids mixing uncommitted journals. Keep file permissions limited to the trusted host account; neither source control nor public Actions is a backup target. Restore to a **new path**, launch with `python -m coordinator --db NEWPATH serve --port UNUSEDPORT`, and confirm revision, proposals and audit against the original before replacing any active database. Do not delete an existing DB to fix a startup failure. Cross-version migration is not implemented; schema changes require an explicit tested migration before release.

There is no UI password-reset or account-deletion flow. Trusted local administrators can revoke sessions or remove access through reviewed database maintenance while stopped; keep historical user references intact. Prefer provisioning named accounts rather than sharing role accounts; public role-account names are for the temporary demo only. To roll back code, stop, back up the database, use a previously validated commit in a separate checkout and test it against a copy. No rollback should erase history.

## Troubleshooting

If disconnected, no mutations are queued. Reconnect and explicitly refresh. If a request failed after being sent, inspect current history rather than assuming it did not commit. A 409 means a different edit or condition update won; refresh and regenerate. A search-limit warning is not an error or proof of infeasibility: reduce exercise size or review the best-found allocation with its gaps. Stand-down conditions require a planner's accurate external assessment, not a bypass. Missing all tasks may simply reflect absent qualifications, inadequate nominal energy or no recorded authorization.

Before distributing an update: verify formatting/indexes, all local tests, audits, exact-head CI and open CodeQL alerts; inspect role boundaries and stale review behavior. Roll back on regression in those critical paths. There is no public production deployment, on-call service, signed installer or operational availability guarantee in this release.
