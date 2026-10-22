"""Jason Stys: measured deterministic synthetic search workload and invariant evidence.

Functions/variable lines: docs/SOURCE_MAP.md. Timing is observational, not an SLO;
hard gates are node bound, honest truncation, deterministic output and feasible plans.
"""

import json
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinator.examples import KINDS, example
from coordinator.models import Assignment, Scenario
from coordinator.planner import NODE_LIMIT, solve, validate_plan
from coordinator.store import timestamp


def dense():
    """Build the maximum list sizes/horizon to exercise the production search cap."""
    data = example().model_dump()
    data["horizon"] = 12
    data["aircraft"] = [
        {**data["aircraft"][0], "id": f"craft-{index}", "battery_percent": 100}
        for index in range(4)
    ]
    data["operators"] = [{**data["operators"][0], "id": f"team-{index}"} for index in range(4)]
    data["tasks"] = [
        {
            **data["tasks"][0],
            "id": f"task-{index}",
            "cell": f"A{index % 4 + 1}",
            "earliest": 0,
            "latest": 12,
            "duration": 1,
            "authorization_recorded": True,
        }
        for index in range(6)
    ]
    return Scenario.model_validate(data)


def main():
    """Measure repeated solver executions; validate outputs separately before reporting success."""
    results = []
    for name, scenario in [*((kind, example(kind)) for kind in KINDS), ("dense", dense())]:
        timings = []
        outputs = []
        for _ in range(3):
            start = time.perf_counter()
            result = solve(scenario)
            timings.append(round((time.perf_counter() - start) * 1000, 3))
            assert result["nodes"] <= NODE_LIMIT
            assert result["optimal"] is not result["truncated"]
            for alternative in result["alternatives"]:
                assert not validate_plan(
                    scenario,
                    [Assignment.model_validate(item) for item in alternative["assignments"]],
                )
            outputs.append(result)
        assert outputs[0] == outputs[1] == outputs[2]
        results.append(
            {
                "scenario": name,
                "milliseconds": timings,
                "median_ms": statistics.median(timings),
                "nodes": outputs[0]["nodes"],
                "truncated": outputs[0]["truncated"],
                "alternatives": len(outputs[0]["alternatives"]),
            }
        )
    report = {
        "at": timestamp(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "node_limit": NODE_LIMIT,
        "results": results,
    }
    path = Path(".runtime/performance.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
