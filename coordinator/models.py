"""Jason Stys: bounded, strict scenario contracts and cross-reference validation.

Functions/classes/variables and physical lines: docs/SOURCE_MAP.md. Slot = five minutes.
Cells are fictional grid squares, not geographic coordinates or navigation instructions.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")]
Label = Annotated[str, Field(min_length=1, max_length=100)]
Sensor = Literal["visual", "thermal", "mapping"]
Cell = Annotated[str, Field(pattern=r"^[A-D][1-4]$")]


class Strict(BaseModel):
    """Reject unknown fields, coercion, NaN and infinity for every external contract."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Aircraft(Strict):
    """Available airframe with nominal endurance, current charge, reserve and sensor list."""

    id: Identifier
    label: Label
    sensors: list[Sensor] = Field(min_length=1, max_length=3)
    available: bool = True
    battery_percent: int = Field(ge=0, le=100)
    reserve_percent: int = Field(ge=20, le=80)
    endurance_minutes: int = Field(ge=5, le=120)


class Operator(Strict):
    """Fictional operator availability and explicitly recorded sensor qualifications."""

    id: Identifier
    label: Label
    qualifications: list[Sensor] = Field(min_length=1, max_length=3)
    available: bool = True


class Task(Strict):
    """Single-cell indivisible observation task; a recorded review is not FAA permission."""

    id: Identifier
    label: Label
    cell: Cell
    sensor: Sensor
    priority: int = Field(ge=1, le=5)
    earliest: int = Field(ge=0, le=11)
    latest: int = Field(ge=1, le=12)
    duration: int = Field(ge=1, le=6)
    authorization_recorded: bool = False

    @model_validator(mode="after")
    def window_fits(self):
        """Validate that the complete task fits within its inclusive/exclusive window."""
        if self.earliest + self.duration > self.latest:
            raise ValueError("task duration does not fit its time window")
        return self


class Conditions(Strict):
    """Conservative incident-wide stop conditions and fictional exclusion grid cells."""

    communications: bool = True
    crewed_aircraft: bool = False
    weather_hold: bool = False
    excluded_cells: list[Cell] = Field(default_factory=list, max_length=16)


class Scenario(Strict):
    """One bounded synthetic planning horizon, never a live emergency/airspace data feed."""

    name: Label
    synthetic: Literal[True] = True
    horizon: int = Field(ge=1, le=12)
    aircraft: list[Aircraft] = Field(max_length=4)
    operators: list[Operator] = Field(max_length=4)
    tasks: list[Task] = Field(max_length=6)
    conditions: Conditions

    @model_validator(mode="after")
    def unique_and_bounded(self):
        """Reject duplicate IDs and task windows extending beyond the selected horizon."""
        for items in (self.aircraft, self.operators, self.tasks):
            ids = [item.id for item in items]
            if len(ids) != len(set(ids)):
                raise ValueError("IDs must be unique within each resource/task list")
        if any(task.latest > self.horizon for task in self.tasks):
            raise ValueError("task window exceeds planning horizon")
        return self


class Assignment(Strict):
    """A planning allocation; there is no vehicle command, waypoint or radio endpoint."""

    task: Identifier
    aircraft: Identifier
    operator: Identifier
    start: int = Field(ge=0, le=11)
    end: int = Field(ge=1, le=12)


class Revision(Strict):
    """Optimistic-concurrency guard for every state-dependent write."""

    revision: int = Field(ge=1)


class Replace(Revision):
    """Whole-scenario replacement allows edits without hidden mutable defaults."""

    scenario: Scenario


class Review(Revision):
    """Named independent human acknowledgement of model limits and coverage gaps."""

    note: str = Field(min_length=10, max_length=500)
    acknowledge_limits: Literal[True]


class Login(Strict):
    """Bounded credentials; passwords are never returned, stored in plaintext or logged."""

    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=1, max_length=128)
