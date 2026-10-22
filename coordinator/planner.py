"""Jason Stys: deterministic bounded top-three resource scheduling and independent validation.

Functions, parameters and assigned-variable line locations: docs/SOURCE_MAP.md.
No travel, detection probabilities, flight physics, flight execution or legal authorization.
"""

import hashlib
import json
from itertools import product

from coordinator.models import Assignment, Scenario

SLOT_MINUTES = 5
NODE_LIMIT = 25000


def digest(value: dict) -> str:
    """Hash canonical JSON for reproducible scenario/plan identity, not secret signing."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def stop_reasons(scenario: Scenario) -> list[str]:
    """List every global hold; none can be overridden by priority or review."""
    conditions = scenario.conditions
    return [
        message
        for blocked, message in (
            (not conditions.communications, "Communications unavailable: stand down"),
            (conditions.crewed_aircraft, "Crewed aircraft activity: stand down"),
            (conditions.weather_hold, "Weather hold: stand down"),
        )
        if blocked
    ]


def budget(aircraft) -> int:
    """Conservative integer available percentage-minutes; avoids float boundary errors."""
    return max(0, aircraft.battery_percent - aircraft.reserve_percent) * aircraft.endurance_minutes


def candidates(scenario: Scenario, task) -> list[Assignment]:
    """Enumerate locally eligible assignments, including full-duration battery feasibility."""
    if (
        stop_reasons(scenario)
        or not task.authorization_recorded
        or task.cell in scenario.conditions.excluded_cells
    ):
        return []
    return [
        Assignment(
            task=task.id,
            aircraft=aircraft.id,
            operator=operator.id,
            start=start,
            end=start + task.duration,
        )
        for start, aircraft, operator in product(
            range(task.earliest, task.latest - task.duration + 1),
            scenario.aircraft,
            scenario.operators,
        )
        if aircraft.available
        and operator.available
        and task.sensor in aircraft.sensors
        and task.sensor in operator.qualifications
        and task.duration * SLOT_MINUTES * 100 <= budget(aircraft)
    ]


def validate_plan(scenario: Scenario, assignments: list[Assignment]) -> list[str]:
    """Revalidate every constraint without relying on solver's candidate generator.

    assignments is bounded by API/schema to six tasks. Returns all observed violations,
    including shared crew, airframe, airspace cell and cumulative nominal energy.
    """
    errors = stop_reasons(scenario) if assignments else []
    tasks = {task.id: task for task in scenario.tasks}
    aircraft = {item.id: item for item in scenario.aircraft}
    operators = {item.id: item for item in scenario.operators}
    seen = set()
    used = {}
    for index, item in enumerate(assignments):
        task, craft, operator = (
            tasks.get(item.task),
            aircraft.get(item.aircraft),
            operators.get(item.operator),
        )
        if task is None or craft is None or operator is None:
            errors.append("Unknown task, aircraft or operator")
            continue
        if item.task in seen:
            errors.append("Duplicate task")
        seen.add(item.task)
        if not (
            task.earliest <= item.start < item.end <= task.latest
            and item.end - item.start == task.duration
        ):
            errors.append("Invalid task interval")
        if not task.authorization_recorded or task.cell in scenario.conditions.excluded_cells:
            errors.append("Missing recorded authorization or excluded cell")
        if not craft.available or not operator.available:
            errors.append("Unavailable resource")
        if task.sensor not in craft.sensors or task.sensor not in operator.qualifications:
            errors.append("Missing sensor or qualification")
        used[craft.id] = used.get(craft.id, 0) + task.duration * SLOT_MINUTES * 100
        for previous in assignments[:index]:
            if previous.task not in tasks:
                continue
            overlap = item.start < previous.end and previous.start < item.end
            shared = (
                item.aircraft == previous.aircraft
                or item.operator == previous.operator
                or task.cell == tasks[previous.task].cell
            )
            if overlap and shared:
                errors.append("Overlapping aircraft, operator or grid cell")
    for craft_id, consumption in used.items():
        if consumption > budget(aircraft[craft_id]):
            errors.append("Cumulative battery reserve violated")
    return sorted(set(errors))


def objective(scenario: Scenario, assignments: list[Assignment]) -> tuple[int, int, int]:
    """Lexicographic maximize covered priority, covered task count, then earlier starts."""
    priorities = {task.id: task.priority for task in scenario.tasks}
    return (
        sum(priorities[item.task] for item in assignments),
        len(assignments),
        -sum(item.start for item in assignments),
    )


def solve(scenario: Scenario, node_limit: int = NODE_LIMIT) -> dict:
    """Search deterministic task/resource choices, retaining top three feasible alternatives.

    Conservative worst-case work O(N*C*T^2 + T*C), where N is at most node_limit
    visited states and C candidates are checked per state. Retained memory O(T*C+T+3*T). Truncation is
    explicit, never described as optimal. T<=6, C<=192, default node_limit=25000.
    """
    tasks = sorted(scenario.tasks, key=lambda task: (-task.priority, task.id))
    options = {task.id: candidates(scenario, task) for task in tasks}
    best = []
    nodes = 0
    truncated = False

    def visit(index, assigned):
        """Depth-first bounded search; skipped tasks ensure a feasible empty fallback."""
        nonlocal nodes, truncated
        if nodes >= node_limit:
            truncated = True
            return
        nodes += 1
        if index == len(tasks):
            key = objective(scenario, assigned)
            serial = [item.model_dump() for item in assigned]
            best.append((key, digest({"assignments": serial}), serial))
            best.sort(key=lambda item: (tuple(-value for value in item[0]), item[1]))
            del best[3:]
            return
        for option in options[tasks[index].id]:
            proposal = [*assigned, option]
            if not validate_plan(scenario, proposal):
                visit(index + 1, proposal)
            if nodes >= node_limit:
                break
        visit(index + 1, assigned)

    visit(0, [])
    if not best:
        best = [((0, 0, 0), digest({"assignments": []}), [])]
    alternatives = []
    for score, identifier, assignments in best:
        assigned_ids = {item["task"] for item in assignments}
        gaps = []
        for task in tasks:
            if task.id not in assigned_ids:
                reason = (
                    "; ".join(stop_reasons(scenario))
                    or ("Authorization not recorded" if not task.authorization_recorded else "")
                    or (
                        "Excluded grid cell"
                        if task.cell in scenario.conditions.excluded_cells
                        else ""
                    )
                    or (
                        "No eligible resource/battery/qualification combination"
                        if not options[task.id]
                        else "Resource/time conflict or search limit; unassigned in this alternative"
                    )
                )
                gaps.append({"task": task.id, "reason": reason})
        alternatives.append(
            {"id": identifier, "score": list(score), "assignments": assignments, "gaps": gaps}
        )
    return {
        "alternatives": alternatives,
        "nodes": nodes,
        "truncated": truncated,
        "optimal": not truncated,
        "holds": stop_reasons(scenario),
    }
