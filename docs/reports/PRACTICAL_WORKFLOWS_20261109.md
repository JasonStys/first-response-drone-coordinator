# Resource-loss exercise workflow validation — 2026-11-09

Jason Stys: saved-scenario planning comparison and observed local validation.

`coordinator/contingency.py` deep-copies one validated synthetic scenario, marks
one available aircraft/operator unavailable, solves both with the same bounded
solver, and compares the first-ranked alternatives. Hashes identify both input
snapshots. The API rejects observers, missing CSRF, stale revisions, unknown or
already unavailable resources, and concurrent saved changes. No persistence API
is called. Existing proposals, reviews, scenario and audit history remain intact.

## Verification

- 109 Python tests passed; 98.30% branch-inclusive coverage; new comparison module
  100%. Independent one-slot exhaustive enumeration proves baseline [9,2,0] and
  single-resource-loss [5,1,0] objectives across both aircraft/operator losses.
- Held scenarios, unavailable/unknown resources, truncation, exact before/after
  source immutability, role/CSRF denial, real concurrent revision changes and no
  persisted evidence mutation are explicitly tested.
- 21 TypeScript tests passed, 100% pure-domain coverage; strict production build
  and 15 three-engine browser journeys passed. They use actual temporary-database API services, real forms,
  planner/reviewer/observer accounts and real downloadable comparison JSON.
- Existing benchmark passed: four ordinary exercises completed 2,789 nodes in
  median 30–40 ms; dense exercise disclosed its 25,000-node cap (median 989 ms).
  Timings describe this machine, not emergency response performance.
- Exact hash-locked Python advisory audit found no known vulnerabilities; live
  OSV npm audit covered all 88 locked identities with zero findings. Ruff,
  formatting, source navigation and output hygiene are retained CI checks.

## Test isolation and boundaries

The expanded browser suite initially exhausted the real 20-attempt/minute login
budget shared across browser engines. Production throttling was not relaxed.
Each engine now has its own disposable database/service on 8862/18862/28862, and
the role-denial test uses that engine's exact configured Origin. The Python
executable is quoted and prefers the repo venv for Windows compatibility.

Only fictional abstract cells/slots/resources are supported. There is no travel,
physical flight/endurance model, actual emergency response, live aircraft, weapons
guidance, legal authorization or dispatch. A review remains human acknowledgement
of a planning exercise. A truncated search may appear better after resource loss
because neither search proves the optimum; the UI explicitly warns about this.
Local validation is not a claim of remote CI completion; publication checks are
performed by the parent worker. No Actions were triggered by this worker.
