"""Jason Stys: saved-scenario resource-loss exercise comparison. Map: docs/SOURCE_MAP.md.

No proposal, review or resource mutation; this does not dispatch aircraft or replace
the existing objective with minimum-change optimization. Variables indexed in map.
"""

from coordinator.models import Scenario
from coordinator.planner import NODE_LIMIT, digest, solve


def preview(scenario: Scenario, kind: str, resource: str, node_limit=NODE_LIMIT):
    """Solve baseline and one unavailable-resource copy with identical search caps and assumptions."""
    if kind not in {"aircraft", "operator"}:
        raise ValueError("Unknown resource kind")
    resources = scenario.aircraft if kind == "aircraft" else scenario.operators
    selected = next((item for item in resources if item.id == resource), None)
    if selected is None:
        raise ValueError("Resource not in saved scenario")
    if not selected.available:
        raise ValueError("Resource is already unavailable")
    changed = scenario.model_copy(deep=True)
    copied = changed.aircraft if kind == "aircraft" else changed.operators
    next(item for item in copied if item.id == resource).available = False
    before, after = solve(scenario, node_limit), solve(changed, node_limit)
    first = {row["task"]: row for row in before["alternatives"][0]["assignments"]}
    second = {row["task"]: row for row in after["alternatives"][0]["assignments"]}
    common = first.keys() & second.keys()
    return {
        "kind": kind,
        "resource": resource,
        "baseline_hash": digest(scenario.model_dump()),
        "outage_hash": digest(changed.model_dump()),
        "before": before,
        "after": after,
        "retained_tasks": sorted(task for task in common if first[task] == second[task]),
        "reassigned_tasks": sorted(task for task in common if first[task] != second[task]),
        "removed_tasks": sorted(first.keys() - second.keys()),
        "added_tasks": sorted(second.keys() - first.keys()),
        "score_delta": [
            b - a
            for a, b in zip(
                before["alternatives"][0]["score"], after["alternatives"][0]["score"], strict=True
            )
        ],
        "comparison_complete": before["optimal"] and after["optimal"],
        "notice": "Read-only synthetic resource-loss exercise. Top alternatives use the existing priority/count/start-time objective, not minimum-change planning. A truncated search cannot establish an optimum or a guaranteed loss bound. No proposal, review or flight authorization created.",
    }
