"""Jason Stys: independent exhaustive oracle, invariant/property and edge-case planning tests.

Test/fixture/variable exact lines: docs/SOURCE_MAP.md. The oracle does NOT call
candidates, validate_plan or objective; enumeration and feasibility are independent.
"""

import itertools
import random

import pytest
from pydantic import ValidationError

from coordinator.examples import KINDS, example
from coordinator.models import Assignment, Scenario
from coordinator.planner import (
    budget,
    candidates,
    digest,
    objective,
    solve,
    stop_reasons,
    validate_plan,
)


def small_case(seed):
    """Generate reproducible bounded cases with tight windows and resource/energy variation."""
    rng = random.Random(seed)  # noqa: S311 - deterministic synthetic fixtures, not secrets
    data = example().model_dump()
    data["horizon"] = 3
    data["tasks"] = data["tasks"][:3]
    for task in data["tasks"]:
        task.update(
            earliest=0,
            latest=3,
            duration=rng.choice([1, 2]),
            priority=rng.randint(1, 5),
            cell=rng.choice(["A1", "B2"]),
            authorization_recorded=rng.choice([True, True, False]),
        )
    for craft in data["aircraft"]:
        craft.update(
            battery_percent=rng.choice([25, 50, 100]), available=rng.choice([True, True, False])
        )
    data["operators"][1]["available"] = rng.choice([True, False])
    return Scenario.model_validate(data)


def oracle(scenario):
    """Enumerate raw choices and independently compute validity and the best objective."""
    choices = []
    for task in scenario.tasks:
        choices.append(
            [None]
            + [
                (task, craft, operator, start)
                for craft, operator, start in itertools.product(
                    scenario.aircraft,
                    scenario.operators,
                    range(task.earliest, task.latest - task.duration + 1),
                )
            ]
        )
    best = (0, 0, 0)
    for raw in itertools.product(*choices):
        rows = [row for row in raw if row is not None]
        valid = True
        for task, craft, operator, _start in rows:
            valid &= bool(
                task.authorization_recorded
                and craft.available
                and operator.available
                and task.sensor in craft.sensors
                and task.sensor in operator.qualifications
                and task.cell not in scenario.conditions.excluded_cells
                and scenario.conditions.communications
                and not scenario.conditions.crewed_aircraft
                and not scenario.conditions.weather_hold
            )
        for left, right in itertools.combinations(rows, 2):
            lt, la, lo, ls = left
            rt, ra, ro, rs = right
            if (
                ls < rs + rt.duration
                and rs < ls + lt.duration
                and (la.id == ra.id or lo.id == ro.id or lt.cell == rt.cell)
            ):
                valid = False
        for craft in scenario.aircraft:
            used = sum(row[0].duration * 5 for row in rows if row[1].id == craft.id)
            if (
                used * 100
                > max(0, craft.battery_percent - craft.reserve_percent) * craft.endurance_minutes
            ):
                valid = False
        if valid:
            best = max(
                best,
                (sum(row[0].priority for row in rows), len(rows), -sum(row[3] for row in rows)),
            )
    return best


@pytest.mark.parametrize("seed", range(30))
def test_independent_oracle(seed):
    """Compare proven-complete small cases to an independently written exhaustive implementation."""
    scenario = small_case(seed)
    result = solve(scenario)
    assert not result["truncated"]
    assert tuple(result["alternatives"][0]["score"]) == oracle(scenario)
    for alternative in result["alternatives"]:
        assert not validate_plan(
            scenario, [Assignment.model_validate(row) for row in alternative["assignments"]]
        )


@pytest.mark.parametrize("kind", KINDS)
def test_templates_deterministic_and_feasible(kind):
    """All supplied exercises reproduce identical alternatives with explicit authorization gaps."""
    scenario = example(kind)
    result = solve(scenario)
    assert result == solve(example(kind))
    assert len(result["alternatives"]) <= 3
    assert any(
        gap["reason"] == "Authorization not recorded" for gap in result["alternatives"][0]["gaps"]
    )
    assert digest(scenario.model_dump()) == digest(
        dict(reversed(list(scenario.model_dump().items())))
    )


@pytest.mark.parametrize(
    "field,value", [("communications", False), ("crewed_aircraft", True), ("weather_hold", True)]
)
def test_stop_gates(field, value):
    """Global holds allocate no tasks and cannot be overridden by validation/review."""
    scenario = example()
    setattr(scenario.conditions, field, value)
    result = solve(scenario)
    assert result["holds"]
    assert result["alternatives"][0]["assignments"] == []
    assert validate_plan(
        scenario, [Assignment(task="sector-1", aircraft="atlas", operator="team-a", start=0, end=2)]
    )


def test_exclusion_and_exhaustion():
    """No aircraft, no crew, empty tasks, excluded cells and flat batteries are valid inputs."""
    scenario = example()
    scenario.conditions.excluded_cells = ["A2"]
    assert "Excluded grid cell" in str(solve(scenario))
    for craft in scenario.aircraft:
        craft.battery_percent = 0
        assert budget(craft) == 0
    assert not solve(scenario)["alternatives"][0]["assignments"]
    scenario.aircraft = []
    scenario.operators = []
    assert not solve(scenario)["alternatives"][0]["assignments"]
    scenario.tasks = []
    assert solve(scenario)["optimal"]


def test_truncation_and_cumulative_budget():
    """Search caps report incomplete optimality and repeated sorties consume shared budget."""
    result = solve(example(), node_limit=1)
    assert result["truncated"] and not result["optimal"] and result["nodes"] == 1
    scenario = example()
    scenario.aircraft[0].battery_percent = 45
    rows = [
        Assignment(task="sector-1", aircraft="atlas", operator="team-a", start=0, end=2),
        Assignment(task="sector-3", aircraft="atlas", operator="team-a", start=2, end=4),
    ]
    assert "Cumulative battery reserve violated" in validate_plan(scenario, rows)


@pytest.mark.parametrize(
    "change,expected",
    [
        ({"task": "unknown"}, "Unknown task, aircraft or operator"),
        ({"end": 1}, "Invalid task interval"),
        ({"start": 3, "end": 5}, "Invalid task interval"),
    ],
)
def test_invalid_assignments(change, expected):
    """Independent validator rejects unknown references and incorrect durations/windows."""
    row = {
        "task": "sector-1",
        "aircraft": "atlas",
        "operator": "team-a",
        "start": 0,
        "end": 2,
        **change,
    }
    assert expected in validate_plan(example(), [Assignment.model_validate(row)])


def test_validator_all_resource_constraints():
    """Check duplicate tasks, collisions, qualification and availability independently."""
    scenario = example()
    one = Assignment(task="sector-1", aircraft="atlas", operator="team-a", start=0, end=2)
    assert "Duplicate task" in validate_plan(scenario, [one, one])
    assert "Overlapping aircraft, operator or grid cell" in validate_plan(scenario, [one, one])
    scenario.aircraft[0].available = False
    scenario.operators[0].qualifications = ["visual"]
    assert "Unavailable resource" in validate_plan(scenario, [one])
    assert "Missing sensor or qualification" in validate_plan(scenario, [one])
    scenario.tasks[0].authorization_recorded = False
    assert "Missing recorded authorization or excluded cell" in validate_plan(scenario, [one])
    assert not candidates(scenario, scenario.tasks[0])
    assert stop_reasons(scenario) == []
    assert objective(scenario, []) == (0, 0, 0)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.update(horizon=0),
        lambda data: data.update(horizon=True),
        lambda data: data.update(synthetic=False),
        lambda data: data.update(extra="ignored?"),
        lambda data: data["tasks"][0].update(duration=6, latest=2),
        lambda data: data["tasks"][0].update(cell="Z99"),
        lambda data: data["tasks"][0].update(latest=12),
        lambda data: data["aircraft"][0].update(reserve_percent=0),
        lambda data: data["aircraft"][0].update(battery_percent=float("nan")),
        lambda data: data["tasks"].append(data["tasks"][0]),
        lambda data: data["operators"].append(data["operators"][0]),
    ],
)
def test_strict_schema(mutate):
    """Reject coercion, unknown fields, duplicates, bad cells, unsafe reserves and unbounded input."""
    data = example().model_dump()
    mutate(data)
    with pytest.raises(ValidationError):
        Scenario.model_validate(data)
