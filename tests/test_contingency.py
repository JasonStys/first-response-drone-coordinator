"""Jason Stys: resource-loss exhaustive tiny oracle and boundary tests. Map: docs/SOURCE_MAP.md."""

from itertools import product

import pytest

from coordinator.contingency import preview
from coordinator.examples import example
from coordinator.models import Scenario


def tiny():
    """Two simultaneous fictional observation tasks, two visual teams and aircraft."""
    original = example().model_dump()
    original["horizon"] = 1
    original["conditions"] = {
        "communications": True,
        "crewed_aircraft": False,
        "weather_hold": False,
        "excluded_cells": [],
    }
    original["tasks"] = [
        {
            "id": f"task-{i}",
            "label": f"Fictional visual check {i}",
            "cell": f"{cell}1",
            "sensor": "visual",
            "priority": priority,
            "earliest": 0,
            "latest": 1,
            "duration": 1,
            "authorization_recorded": True,
        }
        for i, cell, priority in [(1, "A", 5), (2, "B", 4)]
    ]
    for craft in original["aircraft"]:
        craft.update(
            sensors=["visual"],
            available=True,
            battery_percent=100,
            reserve_percent=20,
            endurance_minutes=120,
        )
    for operator in original["operators"]:
        operator.update(qualifications=["visual"], available=True)
    return Scenario.model_validate(original)


def oracle(scenario, kind=None, lost=None):
    """Enumerate all task-to-resource pairs independently for this one-slot oracle fixture."""
    choices = [None] + [
        (craft.id, operator.id)
        for craft in scenario.aircraft
        for operator in scenario.operators
        if craft.available
        and operator.available
        and not (kind == "aircraft" and craft.id == lost)
        and not (kind == "operator" and operator.id == lost)
    ]
    feasible = []
    for assignments in product(choices, repeat=len(scenario.tasks)):
        present = [item for item in assignments if item]
        if len({item[0] for item in present}) != len(present) or len(
            {item[1] for item in present}
        ) != len(present):
            continue
        feasible.append(
            (
                sum(
                    task.priority
                    for task, item in zip(scenario.tasks, assignments, strict=True)
                    if item
                ),
                len(present),
                0,
            )
        )
    return list(max(feasible))


@pytest.mark.parametrize("kind", ["aircraft", "operator"])
def test_outage_matches_independent_exhaustive_oracle_without_mutation(kind):
    scenario = tiny()
    before = scenario.model_dump_json()
    resources = scenario.aircraft if kind == "aircraft" else scenario.operators
    for resource in resources:
        result = preview(scenario, kind, resource.id)
        assert result["before"]["alternatives"][0]["score"] == oracle(scenario) == [9, 2, 0]
        assert (
            result["after"]["alternatives"][0]["score"]
            == oracle(scenario, kind, resource.id)
            == [5, 1, 0]
        )
        assert result["removed_tasks"] == ["task-2"]
        assert result["score_delta"] == [-4, -1, 0]
        assert result["comparison_complete"]
        assert result["baseline_hash"] != result["outage_hash"]
        for row in result["after"]["alternatives"][0]["assignments"]:
            assert row[kind] != resource.id
    assert scenario.model_dump_json() == before


def test_holds_already_unavailable_unknown_and_search_limit():
    scenario = tiny()
    resource = scenario.aircraft[0].id
    limited = preview(scenario, "aircraft", resource, node_limit=1)
    assert not limited["comparison_complete"]
    assert limited["before"]["truncated"]
    scenario.conditions.weather_hold = True
    held = preview(scenario, "aircraft", resource)
    assert held["before"]["alternatives"][0]["assignments"] == []
    assert held["after"]["alternatives"][0]["assignments"] == []
    assert held["after"]["holds"]
    with pytest.raises(ValueError, match="kind"):
        preview(scenario, "sensor", resource)
    with pytest.raises(ValueError, match="not in"):
        preview(scenario, "operator", "unknown")
    scenario.aircraft[0].available = False
    with pytest.raises(ValueError, match="already"):
        preview(scenario, "aircraft", resource)
