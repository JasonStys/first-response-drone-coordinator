"""Jason Stys: real application/session/SQLite security and concurrent revision tests.

Fixtures/tests and variable locations: docs/SOURCE_MAP.md. Credentials are synthetic,
created in fresh isolated test databases; no host accounts or network calls are used.
"""

import hashlib
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from coordinator.api import create_app
from coordinator.auth import add_user
from coordinator.examples import example
from coordinator.models import Scenario
from coordinator.planner import solve
from coordinator.store import Store

ORIGIN = "http://127.0.0.1:8861"
PASSWORD = "Only-synthetic-tests-2026!"


@pytest.fixture
def app(tmp_path):
    """Build an actual service and all three roles in a fresh temporary database."""
    service = create_app(tmp_path / "workspace.db")
    service.state.store.initialize(example())
    for role in ("planner", "reviewer", "observer"):
        add_user(service.state.store, role, PASSWORD, role)
    return service


def client(app, role="planner"):
    """Authenticate a real cookie session and retain its per-session CSRF header."""
    browser = TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN})
    response = browser.post("/api/login", json={"username": role, "password": PASSWORD})
    assert response.status_code == 200
    browser.headers["X-CSRF-Token"] = response.json()["csrf"]
    return browser


def generate(browser):
    """Generate against the currently observed revision using the public API."""
    workspace = browser.get("/api/workspace").json()
    result = browser.post("/api/proposals", json={"revision": workspace["revision"]})
    assert result.status_code == 200
    return result.json()


def test_workflow_review_invalidation_and_export(app):
    """Exercise authoring, independent human review, persistence, export and stale protection."""
    planner, reviewer = client(app), client(app, "reviewer")
    proposal = generate(planner)
    selected = proposal["result"]["alternatives"][0]["id"]
    endpoint = f"/api/proposals/{proposal['id']}/review/{selected}"
    body = {
        "revision": 1,
        "note": "Checked gaps and nominal model limitations.",
        "acknowledge_limits": True,
    }
    assert planner.post(endpoint, json=body).status_code == 403
    assert reviewer.post(endpoint, json=body).json()["flight_authorization"] is False
    assert reviewer.post(endpoint, json=body).status_code == 409
    state = planner.get("/api/workspace").json()
    scenario = state["scenario"]
    scenario["conditions"]["crewed_aircraft"] = True
    assert (
        planner.put("/api/workspace", json={"revision": 1, "scenario": scenario}).json()["revision"]
        == 2
    )
    assert (
        planner.put("/api/workspace", json={"revision": 1, "scenario": scenario}).status_code == 409
    )
    assert planner.post("/api/proposals", json={"revision": 1}).status_code == 409
    assert reviewer.post(endpoint, json={**body, "revision": 2}).status_code == 409
    report = reviewer.get("/api/report")
    assert report.headers["content-disposition"].startswith("attachment")
    assert report.json()["proposals"][0]["stale"] is True
    assert "No aircraft dispatched" in report.json()["notice"]
    assert {row["event"] for row in report.json()["audit"]} == {
        "proposal_generated",
        "planning_review_recorded",
        "scenario_replaced",
    }
    blocked = generate(planner)
    assert blocked["result"]["alternatives"][0]["assignments"] == []
    selected = blocked["result"]["alternatives"][0]["id"]
    assert (
        reviewer.post(
            f"/api/proposals/{blocked['id']}/review/{selected}", json={**body, "revision": 2}
        ).status_code
        == 409
    )
    reopened = Store(app.state.store.path)
    assert reopened.snapshot()[0] == 2
    reopened.initialize(example("flood"))
    assert reopened.snapshot()[1].conditions.crewed_aircraft


def test_authentication_roles_cookie_and_revocation(app):
    """Anonymous reads, wrong roles, missing CSRF, expiration and sign-out fail closed."""
    anonymous = TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN})
    for path in ("workspace", "me", "report", "examples"):
        assert anonymous.get(f"/api/{path}").status_code == 401
    assert anonymous.get("/healthz").json()["status"] == "ok"
    assert anonymous.get("/openapi.json").status_code == 404
    bad = anonymous.post("/api/login", json={"username": "planner", "password": "wrong"})
    assert bad.status_code == 401
    assert (
        anonymous.post("/api/login", json={"username": "missing", "password": "wrong"}).status_code
        == 401
    )
    observer = client(app, "observer")
    assert observer.get("/api/me").json()["role"] == "observer"
    assert observer.post("/api/proposals", json={"revision": 1}).status_code == 403
    assert (
        observer.put(
            "/api/workspace", json={"revision": 1, "scenario": example().model_dump()}
        ).status_code
        == 403
    )
    planner = client(app)
    token = planner.cookies["response_session"]
    assert any(cookie.has_nonstandard_attr("HttpOnly") for cookie in planner.cookies.jar)
    with app.state.store.connect() as db:
        rows = db.execute("SELECT * FROM sessions").fetchall()
        assert all(row["digest"] != token for row in rows)
        assert (
            db.execute("SELECT password_hash FROM users LIMIT 1")
            .fetchone()[0]
            .startswith("$argon2id$")
        )
    planner.headers.pop("X-CSRF-Token")
    assert planner.post("/api/logout", json={}).status_code == 403
    planner.headers["X-CSRF-Token"] = planner.get("/api/me").json()["csrf"]
    assert planner.post("/api/logout", json={}).status_code == 200
    planner.cookies.set("response_session", token)
    assert planner.get("/api/me").status_code == 401
    observer_token = observer.cookies["response_session"]
    with app.state.store.connect(True) as db:
        db.execute(
            "UPDATE sessions SET expires = ? WHERE digest = ?",
            (time.time() - 1, hashlib.sha256(observer_token.encode()).hexdigest()),
        )
    assert observer.get("/api/me").status_code == 401
    observer.cookies.set("response_session", "x" * 101)
    assert observer.get("/api/me").status_code == 401


def test_security_boundary_and_strict_input(app):
    """Origin/Host/CSRF/body limits, SQL injection strings and validation reflection are tested."""
    planner = client(app)
    for origin in ("https://evil.invalid", "null", ""):
        assert (
            planner.post(
                "/api/proposals", json={"revision": 1}, headers={"Origin": origin}
            ).status_code
            == 403
        )
    assert planner.get("/healthz", headers={"Host": "evil.invalid"}).status_code == 400
    assert (
        planner.post(
            "/api/proposals", json={"revision": 1}, headers={"Sec-Fetch-Site": "cross-site"}
        ).status_code
        == 403
    )
    assert (
        planner.post(
            "/api/proposals", content="text", headers={"Content-Type": "text/plain"}
        ).status_code
        == 415
    )
    assert (
        planner.post(
            "/api/proposals", content="x" * 70000, headers={"Content-Type": "application/json"}
        ).status_code
        == 413
    )
    assert (
        planner.post(
            "/api/proposals",
            content=iter([b"x" * 30000, b"x" * 40000]),
            headers={"Content-Type": "application/json"},
        ).status_code
        == 413
    )
    invalid = planner.post(
        "/api/login", json={"username": "a", "password": "DO-NOT-REFLECT", "extra": True}
    )
    assert invalid.status_code == 422 and "DO-NOT-REFLECT" not in invalid.text
    assert planner.post("/api/proposals", json={"revision": "1"}).status_code == 422
    assert (
        planner.post(
            "/api/login", json={"username": "' OR 1=1 --", "password": "wrong"}
        ).status_code
        == 401
    )
    assert set(planner.get("/api/examples").json()) == {
        "wildfire",
        "flood",
        "search",
        "restoration",
    }
    headers = planner.get("/healthz").headers
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert not headers.get("access-control-allow-origin")
    assert planner.get("/assets/../../coordinator/schema.sql").status_code == 404


def test_login_throttle_and_secure_cookie(app):
    """Persistent per-direct-client attempt cap and secure HTTPS cookie behavior."""
    browser = client(app)
    with app.state.store.connect(True) as db:
        db.execute("UPDATE attempts SET count = 20")
    assert (
        browser.post("/api/login", json={"username": "planner", "password": PASSWORD}).status_code
        == 429
    )
    with app.state.store.connect(True) as db:
        db.execute("UPDATE attempts SET started = ?", (time.time() - 61,))
    assert (
        browser.post("/api/login", json={"username": "planner", "password": PASSWORD}).status_code
        == 200
    )
    secure = create_app(app.state.store.path, "https://exercise.invalid")
    secure_browser = TestClient(
        secure, base_url="https://exercise.invalid", headers={"Origin": "https://exercise.invalid"}
    )
    response = secure_browser.post("/api/login", json={"username": "planner", "password": PASSWORD})
    cookie = response.headers["set-cookie"].lower()
    assert all(
        value in cookie for value in ("httponly", "samesite=strict", "secure", "max-age=3600")
    )
    assert response.headers["strict-transport-security"].startswith("max-age=")


@pytest.mark.parametrize(
    "username,password,role",
    [
        ("bad space", PASSWORD, "planner"),
        ("valid", "short", "observer"),
        ("valid", PASSWORD, "admin"),
    ],
)
def test_provision_validation(app, username, password, role):
    """No arbitrary roles, weak CLI passwords or unsafe username forms."""
    with pytest.raises(ValueError):
        add_user(app.state.store, username, password, role)
    with pytest.raises(sqlite3.IntegrityError):
        add_user(app.state.store, "planner", PASSWORD, "planner")


def test_concurrent_revision_and_compute_race(app):
    """Exactly one concurrent editor wins; stale computed proposals cannot be saved."""
    store = app.state.store

    def change(_):
        """Attempt one independent serialized write using the same expected revision."""
        try:
            return store.replace(1, example("flood"), "planner")
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(change, range(4)))
    assert sorted(results) == [2, 409, 409, 409]
    with pytest.raises(HTTPException, match="409"):
        store.save_proposal(1, example(), solve(example()), "planner")


def test_review_identity_and_tamper_revalidation(app):
    """The persistence boundary independently checks author identity and plan contents."""
    store = app.state.store
    result = solve(example())
    identifier = store.save_proposal(1, example(), result, "reviewer")
    selected = result["alternatives"][0]["id"]
    with pytest.raises(HTTPException, match="403"):
        store.review(identifier, selected, 1, "reviewer", "Self review denied")
    with pytest.raises(HTTPException, match="404"):
        store.review(9999, selected, 1, "planner", "Unknown proposal")
    with pytest.raises(HTTPException, match="404"):
        store.review(identifier, "unknown", 1, "planner", "Unknown alternative")
    result["alternatives"][0]["assignments"][0]["task"] = "unknown"
    import json

    with store.connect(True) as db:
        db.execute("UPDATE proposals SET result = ? WHERE id = ?", (json.dumps(result), identifier))
    with pytest.raises(HTTPException, match="409"):
        store.review(identifier, selected, 1, "planner", "Tampered plan denied")


@pytest.mark.parametrize(
    "origin",
    [
        "file:///tmp",
        "http://example.test/path",
        "http://example.test?x=y",
        "https://user@example.test",
    ],
)
def test_invalid_origin(tmp_path, origin):
    """Unsafe trusted-origin configuration is rejected at startup."""
    with pytest.raises(ValueError):
        create_app(tmp_path / "unused.db", origin)


def test_uninitialized_service(tmp_path):
    """Service without initialized workspace fails explicitly, not with invented defaults."""
    service = create_app(tmp_path / "new.db")
    with pytest.raises(HTTPException, match="503"):
        service.state.store.snapshot()
    assert isinstance(Scenario.model_validate(example().model_dump()), Scenario)
