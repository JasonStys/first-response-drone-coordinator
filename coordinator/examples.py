"""Jason Stys: four fictional exercise templates without real people or incident coordinates.

Function/variable locations: docs/SOURCE_MAP.md. Nominal resource values are invented,
not manufacturer specifications. Search means area observation, not person identification.
"""

from coordinator.models import Scenario

KINDS = {
    "wildfire": (
        "Wildfire perimeter exercise",
        "thermal",
        [
            "North perimeter observation",
            "Evacuation route overview",
            "Cooling area inspection",
            "Access corridor mapping",
        ],
    ),
    "flood": (
        "Flood assessment exercise",
        "mapping",
        [
            "Bridge approach assessment",
            "Levee overview",
            "Utility access assessment",
            "Drainage corridor mapping",
        ],
    ),
    "search": (
        "Missing-person search planning exercise",
        "thermal",
        [
            "Sector overview A",
            "Sector overview B",
            "Trail access overview",
            "Staging area overview",
        ],
    ),
    "restoration": (
        "Infrastructure restoration exercise",
        "visual",
        [
            "Substation exterior overview",
            "Access road assessment",
            "Pole corridor overview",
            "Bridge exterior mapping",
        ],
    ),
}


def example(kind="wildfire") -> Scenario:
    """Build fresh validated resources and tasks; no shared mutable template instances."""
    name, sensor, labels = KINDS[kind]
    return Scenario.model_validate(
        {
            "name": name,
            "synthetic": True,
            "horizon": 8,
            "aircraft": [
                {
                    "id": "atlas",
                    "label": "Atlas / multirole",
                    "sensors": ["visual", "thermal", "mapping"],
                    "available": True,
                    "battery_percent": 90,
                    "reserve_percent": 25,
                    "endurance_minutes": 50,
                },
                {
                    "id": "swift",
                    "label": "Swift / observation",
                    "sensors": ["visual", sensor],
                    "available": True,
                    "battery_percent": 75,
                    "reserve_percent": 25,
                    "endurance_minutes": 40,
                },
            ],
            "operators": [
                {
                    "id": "team-a",
                    "label": "Exercise team A",
                    "qualifications": ["visual", "thermal", "mapping"],
                    "available": True,
                },
                {
                    "id": "team-b",
                    "label": "Exercise team B",
                    "qualifications": ["visual", sensor],
                    "available": True,
                },
            ],
            "tasks": [
                {
                    "id": f"sector-{index + 1}",
                    "label": label,
                    "cell": ["A2", "B3", "C2", "D3"][index],
                    "sensor": sensor if index < 2 else "visual",
                    "priority": 5 - index,
                    "earliest": 0 if index < 2 else 2,
                    "latest": 4 if index < 2 else 8,
                    "duration": 2,
                    "authorization_recorded": index != 3,
                }
                for index, label in enumerate(labels)
            ],
            "conditions": {
                "communications": True,
                "crewed_aircraft": False,
                "weather_hold": False,
                "excluded_cells": [],
            },
        }
    )
