"""Jason Stys: Argon2id, opaque expiring sessions, roles and persistent login throttling.

Exact declaration/variable locations: docs/SOURCE_MAP.md. No external identity services.
"""

import hashlib
import hmac
import re
import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import HTTPException, Request

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
DUMMY = HASHER.hash("not-a-user-timing-equalizer")


def add_user(store, username, password, role):
    """CLI-only provisioning; existing names cannot be silently overwritten."""
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,39}", username) or role not in (
        "planner",
        "reviewer",
        "observer",
    ):
        raise ValueError(
            "Use a lowercase 3–40 character username and planner/reviewer/observer role"
        )
    if not 14 <= len(password) <= 128:
        raise ValueError("Password must contain 14–128 characters")
    hashed = HASHER.hash(password)
    with store.connect(True) as db:
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hashed, role))


def sign_in(request: Request, username, password):
    """Throttle all attempts per direct client address and issue a freshly rotated session."""
    store = request.app.state.store
    now = time.time()
    client = hashlib.sha256(
        (request.client.host if request.client else "unknown").encode()
    ).hexdigest()
    with store.connect(True) as db:
        db.execute("DELETE FROM attempts WHERE started < ?", (now - 60,))
        row = db.execute("SELECT count FROM attempts WHERE client = ?", (client,)).fetchone()
        if row and row["count"] >= 20:
            raise HTTPException(429, "Too many sign-in attempts; wait one minute")
        if not row and db.execute("SELECT count(*) FROM attempts").fetchone()[0] >= 1000:
            raise HTTPException(429, "Sign-in capacity reached; wait one minute")
        db.execute(
            "INSERT INTO attempts VALUES (?, 1, ?) ON CONFLICT(client) DO UPDATE SET count = count + 1",
            (client, now),
        )
        user = db.execute("SELECT * FROM users WHERE name = ?", (username,)).fetchone()
    try:
        HASHER.verify(user["password_hash"] if user else DUMMY, password)
    except VerificationError as error:
        raise HTTPException(401, "Invalid credentials") from error
    if user is None:
        raise HTTPException(401, "Invalid credentials")
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with store.connect(True) as db:
        db.execute("DELETE FROM sessions WHERE expires < ?", (now,))
        db.execute(
            "DELETE FROM sessions WHERE username = ? AND digest NOT IN (SELECT digest FROM sessions WHERE username = ? ORDER BY created DESC LIMIT 9)",
            (username, username),
        )
        db.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
            (hashlib.sha256(token.encode()).hexdigest(), username, csrf, now + 3600, now),
        )
    return token, {"name": username, "role": user["role"], "csrf": csrf}


def identity(request: Request):
    """Resolve current server-side role and absolute session expiry; cookie contents have no roles."""
    token = request.cookies.get("response_session", "")
    if not 20 <= len(token) <= 100:
        raise HTTPException(401, "Sign in to the private workspace")
    with request.app.state.store.connect() as db:
        row = db.execute(
            "SELECT username AS name, role, csrf FROM sessions JOIN users ON username = users.name WHERE digest = ? AND expires > ?",
            (hashlib.sha256(token.encode()).hexdigest(), time.time()),
        ).fetchone()
    if row is None:
        raise HTTPException(401, "Session expired or revoked")
    return dict(row)


def authorize(request: Request, role=None):
    """For writes require role plus session CSRF; same-origin is enforced before routing."""
    user = identity(request)
    if role is not None and user["role"] != role:
        raise HTTPException(403, f"{role.capitalize()} role required")
    if not hmac.compare_digest(
        request.headers.get("x-csrf-token", "").encode(), user["csrf"].encode()
    ):
        raise HTTPException(403, "CSRF token required")
    return user


def sign_out(request: Request):
    """Revoke only this session, immediately invalidating its cookie and CSRF value."""
    authorize(request)
    with request.app.state.store.connect(True) as db:
        db.execute(
            "DELETE FROM sessions WHERE digest = ?",
            (hashlib.sha256(request.cookies["response_session"].encode()).hexdigest(),),
        )
