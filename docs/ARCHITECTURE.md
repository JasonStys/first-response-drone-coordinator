# Architecture and decisions

By Jason Stys. Accepted 2026-10-21 for a bounded portfolio exercise, not a production emergency deployment.

## Requirements and data flow

One trusted exercise workspace contains aircraft, nominal energy parameters, operator qualifications, observation tasks and manually entered conditions. Planners change scenarios and generate proposals; independent reviewers record planning review; observers read. Data must persist locally, stale writes must fail, altered conditions must invalidate earlier review, and generated plans must explain unassigned tasks.

```text
React/TypeScript UI → exact-origin FastAPI boundary → session/role/CSRF checks
                                          ├→ strict scenario schema → bounded search
                                          │                            ↓
                                          └→ revision-guarded SQLite transaction
                                                     ↓
                                         proposals + review + audit → JSON evidence
```

No external control plane, live data source, image analysis, person identification or vehicle connection exists. All fictional cells use a four-by-four grid. Time is relative to the exercise epoch, not a real departure timestamp.

## ADR-001: language and persistence boundaries

**Decision:** TypeScript/React for UI state and typed presentation; Python/FastAPI/Pydantic for strict contracts and bounded search; parameterized SQLite SQL for durable local transactions. Browser and API share one origin.

Alternatives: a Node-only service reduces languages but does not improve the independent Python oracle story; PostgreSQL/PostGIS enables geographic/distributed applications but adds an unnecessary server and suggests a level of spatial fidelity this exercise does not have. SQLite keeps setup small. No claim is made that this version scales horizontally or supports separate tenants. Revisit persistence and identity management before introducing distributed teams or real incident data.

## ADR-002: deterministic bounded alternatives instead of LLM decisions

Enumerate each task's eligible aircraft/operator/start choices and its skip choice. Visit high-priority tasks first, sort equal priorities by stable task ID, and keep three best leaf solutions. The lexicographic objective maximizes sum of allocated priorities, then allocated task count, then minimizes sum of start slots. This is a transparent exercise objective, **not** a real emergency triage algorithm. Tie-breaking uses canonical assignment hashes, not wall-clock order.

Constraints: task window and duration; recorded authorization flag; cell exclusions; available airframes and operators; matching sensor and qualification; nonoverlap on shared airframe, operator or cell; cumulative nominal energy use across tasks. Available percentage-minutes are `max(0, charge-reserve)*nominal_endurance`; demand is `duration_slots*5*100`. Integer arithmetic avoids floating-point reserve boundary errors. No recharge, transit, weather-dependent endurance or mission physics is inferred.

Maximum T=6 tasks, C≤192 candidates per task, horizon≤12 slots, 4 aircraft/4 operators. At most N=25,000 visited states by default; no request can raise the cap. A conservative work bound is O(N*C*T² + T*C); memory O(T*C + T + K*T), K=3. Results say `truncated=true, optimal=false` if the cap interrupts enumeration. Exhaustive small cases can claim objective optimality **only within this model**. Coverage gaps distinguish holds, missing authorization, exclusions, no eligible combination and conflicts/search limits; they do not invent a unique causal proof for combinatorial infeasibility.

Alternatives such as an unbounded optimizer or external LLM complicate latency and reproducibility. This search is intentionally small, deterministic, and checked against an independently implemented exhaustive oracle. Before increasing limits, measure worst-case work and introduce an appropriate bounded solver with cancellation and load isolation.

## ADR-003: immutable revision snapshots and independent review

An edit increments the scenario revision under `BEGIN IMMEDIATE`. A proposal calculated outside the transaction is saved only if the revision still matches. A reviewer must be different from the proposal creator, use the reviewer role, select an existing alternative, acknowledge limits and provide a note. Review rechecks the current scenario hash and independently validates the stored assignments. Empty or infeasible plans cannot be reviewed. Review plus audit event commits atomically. Historical reviews remain stored but are stale after any edit, even if the new scenario happens to have identical content.

Hard holds cannot be overridden by task priority, missing coverage, or a reviewer. Emergency conditions do not automatically provide aviation permission. The manual authorization flag only records that a planner says an external review occurred; the software cannot verify or grant that permission.

## Reliability and scale assumptions

SQLite serializes writes with a ten-second busy timeout. Concurrent same-revision edits permit one winner; others receive 409 and must refresh. Queries return the latest 20 proposals and 100 audit events; the database itself grows until the trusted host manages archival. A browser disconnect does not queue mutations and requires an explicit fresh snapshot after reconnection. Loss of incident communications is separately modeled as a server-enforced global hold.

This is one local service and trusted workspace, not a replicated system. Back up the database while stopped, test restores, retain OS access controls and avoid network exposure. Revisit worker isolation, per-account quotas, database migrations, identity federation, audit export integrity, retention, accessibility and domain validation before any production adaptation.
