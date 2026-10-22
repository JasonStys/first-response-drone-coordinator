"""Jason Stys: parameterized SQLite transactions, revision checks and bounded audit reads.

Exact function/variable locations: docs/SOURCE_MAP.md. Private DB stays outside Git.
The OS/database owner is trusted; audit rows are not a tamper-proof external ledger.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException

from coordinator.models import Scenario
from coordinator.planner import digest, validate_plan


def timestamp():
    """Create explicit UTC ISO timestamps for chronological human review evidence."""
    return datetime.now(UTC).isoformat()


class Store:
    """One local workspace per database; transactions serialize concurrent state writes."""

    def __init__(self, path: Path):
        """Initialize an idempotent version-one database at an explicitly selected path."""
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))

    @contextmanager
    def connect(self, write=False):
        """Close every connection, committing successful writes and rolling back exceptions."""
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        finally:
            db.close()

    def initialize(self, scenario: Scenario):
        """Seed synthetic data only once; never overwrite an existing workspace on startup."""
        with self.connect(True) as db:
            db.execute(
                "INSERT OR IGNORE INTO workspace VALUES (1, 1, ?, 1)", (scenario.model_dump_json(),)
            )

    def snapshot(self, db=None):
        """Return a coherent revision/scenario snapshot, optionally in the caller transaction."""
        if db is None:
            with self.connect() as connection:
                return self.snapshot(connection)
        row = db.execute("SELECT revision, scenario FROM workspace WHERE id = 1").fetchone()
        if row is None:
            raise HTTPException(503, "Initialize the workspace with the local CLI")
        return row["revision"], Scenario.model_validate_json(row["scenario"])

    def event(self, db, actor, event, revision, detail):
        """Append structured non-secret evidence inside the same atomic state transaction."""
        db.execute(
            "INSERT INTO audit(at, actor, event, revision, detail) VALUES (?, ?, ?, ?, ?)",
            (timestamp(), actor, event, revision, detail),
        )

    def check_revision(self, db, expected):
        """Reject stale writes, including proposals computed before a concurrent edit."""
        revision, scenario = self.snapshot(db)
        if revision != expected:
            raise HTTPException(409, "Workspace changed: refresh and generate a new proposal")
        return scenario

    def replace(self, expected, scenario, actor):
        """Increment the workspace revision; older approvals become visibly stale, never deleted."""
        with self.connect(True) as db:
            self.check_revision(db, expected)
            db.execute(
                "UPDATE workspace SET revision = revision + 1, scenario = ? WHERE id = 1",
                (scenario.model_dump_json(),),
            )
            self.event(db, actor, "scenario_replaced", expected + 1, scenario.name)
        return expected + 1

    def save_proposal(self, revision, scenario, result, actor):
        """Persist solver output only against the exact still-current scenario revision."""
        with self.connect(True) as db:
            self.check_revision(db, revision)
            cursor = db.execute(
                "INSERT INTO proposals(revision, creator, scenario_hash, result, created) VALUES (?, ?, ?, ?, ?)",
                (revision, actor, digest(scenario.model_dump()), json.dumps(result), timestamp()),
            )
            self.event(db, actor, "proposal_generated", revision, str(cursor.lastrowid))
            return cursor.lastrowid

    def review(self, identifier, selected, expected, actor, note):
        """Require independent review, current snapshot, feasible non-empty selected plan."""
        from coordinator.models import Assignment

        with self.connect(True) as db:
            scenario = self.check_revision(db, expected)
            row = db.execute("SELECT * FROM proposals WHERE id = ?", (identifier,)).fetchone()
            if row is None:
                raise HTTPException(404, "Proposal not found")
            if row["revision"] != expected or row["scenario_hash"] != digest(scenario.model_dump()):
                raise HTTPException(409, "Proposal is stale")
            if row["creator"] == actor:
                raise HTTPException(403, "A different reviewer must review the proposal")
            if row["reviewed_by"]:
                raise HTTPException(409, "Proposal already reviewed")
            alternative = next(
                (
                    item
                    for item in json.loads(row["result"])["alternatives"]
                    if item["id"] == selected
                ),
                None,
            )
            if alternative is None:
                raise HTTPException(404, "Alternative not found")
            assignments = [Assignment.model_validate(item) for item in alternative["assignments"]]
            if not assignments or validate_plan(scenario, assignments):
                raise HTTPException(
                    409, "No feasible assignments to review; holds cannot be overridden"
                )
            db.execute(
                "UPDATE proposals SET reviewed_by = ?, selected = ?, note = ? WHERE id = ?",
                (actor, selected, note, identifier),
            )
            self.event(
                db,
                actor,
                "planning_review_recorded",
                expected,
                f"proposal {identifier}; alternative {selected}",
            )

    def history(self):
        """Read newest twenty proposals and newest one hundred audit events in bounded queries."""
        with self.connect() as db:
            proposals = [
                dict(row) for row in db.execute("SELECT * FROM proposals ORDER BY id DESC LIMIT 20")
            ]
            events = [
                dict(row) for row in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")
            ]
        for proposal in proposals:
            proposal["result"] = json.loads(proposal["result"])
        return proposals, events
