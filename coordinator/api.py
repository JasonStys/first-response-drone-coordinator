"""Jason Stys: same-origin authenticated advisory API, security boundary and static frontend.

Exact declaration/variable locations: docs/SOURCE_MAP.md. No drone/radio/third-party APIs.
"""

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from coordinator import auth
from coordinator.examples import KINDS, example
from coordinator.models import Login, Replace, Review, Revision
from coordinator.planner import solve
from coordinator.store import Store

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 65536
HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cache-Control": "no-store",
}


def create_app(database: Path, origin="http://127.0.0.1:8861"):
    """Build one local workspace service; an exact trusted origin is mandatory for mutations."""
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
    ):
        raise ValueError("Origin must be an exact HTTP(S) scheme and authority without path")
    app = FastAPI(
        title="First Response Drone Coordinator", docs_url=None, redoc_url=None, openapi_url=None
    )
    app.state.store = Store(database)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        """Do not reflect credential fields or arbitrary uploaded values in validation responses."""
        return JSONResponse(
            {"detail": "Invalid fields, types, IDs, bounds or time windows"}, status_code=422
        )

    @app.middleware("http")
    async def security(request: Request, call_next):
        """Bound even streamed bodies, reject hostile Host/origin and attach restrictive headers."""
        response = None
        if request.headers.get("host") != parsed.netloc:
            response = JSONResponse({"detail": "Untrusted Host"}, status_code=400)
        elif request.method not in ("GET", "HEAD", "OPTIONS") and (
            request.headers.get("origin") != origin
            or request.headers.get("sec-fetch-site") == "cross-site"
        ):
            response = JSONResponse(
                {"detail": "Exact same-origin request required"}, status_code=403
            )
        elif request.method not in ("GET", "HEAD", "OPTIONS"):
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                response = JSONResponse({"detail": "JSON required"}, status_code=415)
            else:
                chunks = []
                size = 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BODY:
                        response = JSONResponse({"detail": "Body too large"}, status_code=413)
                        break
                    chunks.append(chunk)
                if response is None:
                    # Starlette's cached Request body is forwarded by BaseHTTPMiddleware.
                    request._body = b"".join(chunks)
        if response is None:
            response = await call_next(request)
        response.headers.update(HEADERS)
        if parsed.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/healthz")
    def health():
        """Anonymous liveness contains no workspace, account or incident data."""
        return {"status": "ok", "mode": "synthetic-planning-only"}

    @app.post("/api/login")
    def login(body: Login, request: Request):
        """Validate login and issue HttpOnly SameSite=Strict cookie, Secure under HTTPS."""
        token, user = auth.sign_in(request, body.username, body.password)
        response = JSONResponse(user)
        response.set_cookie(
            "response_session",
            token,
            httponly=True,
            samesite="strict",
            secure=parsed.scheme == "https",
            max_age=3600,
        )
        return response

    @app.get("/api/me")
    def me(request: Request):
        """Return only the current session identity and CSRF value."""
        return auth.identity(request)

    @app.post("/api/logout")
    def logout(request: Request):
        """Immediately revoke the authenticated session, not just the browser cookie."""
        auth.sign_out(request)
        response = JSONResponse({"signed_out": True})
        response.delete_cookie("response_session")
        return response

    @app.get("/api/workspace")
    def workspace(request: Request):
        """Authenticated coherent current snapshot plus bounded proposal/audit history."""
        auth.identity(request)
        revision, scenario = app.state.store.snapshot()
        proposals, events = app.state.store.history()
        return {
            "revision": revision,
            "scenario": scenario.model_dump(),
            "proposals": proposals,
            "audit": events,
        }

    @app.get("/api/examples")
    def examples(request: Request):
        """Return fictional exercise templates only to authenticated workspace users."""
        auth.identity(request)
        return {kind: example(kind).model_dump() for kind in KINDS}

    @app.put("/api/workspace")
    def replace(body: Replace, request: Request):
        """Planner-only condition/resource edits always invalidate old planning reviews."""
        user = auth.authorize(request, "planner")
        revision = app.state.store.replace(body.revision, body.scenario, user["name"])
        return {"revision": revision}

    @app.post("/api/proposals")
    def propose(body: Revision, request: Request):
        """Compute bounded alternatives, then atomically reject concurrent stale persistence."""
        user = auth.authorize(request, "planner")
        revision, scenario = app.state.store.snapshot()
        if revision != body.revision:
            raise HTTPException(409, "Refresh stale workspace")
        result = solve(scenario)
        identifier = app.state.store.save_proposal(revision, scenario, result, user["name"])
        return {"id": identifier, "result": result}

    @app.post("/api/proposals/{identifier}/review/{selected}")
    def review(identifier: int, selected: str, body: Review, request: Request):
        """Reviewer-only independent acknowledgement, never operational flight approval."""
        user = auth.authorize(request, "reviewer")
        app.state.store.review(identifier, selected, body.revision, user["name"], body.note)
        return {"status": "planning_review_recorded", "flight_authorization": False}

    @app.get("/api/report")
    def report(request: Request):
        """Export portable JSON evidence with explicit stale markers and planning-only scope."""
        data = workspace(request)
        for proposal in data["proposals"]:
            proposal["stale"] = proposal["revision"] != data["revision"]
        data["notice"] = (
            "SYNTHETIC PLANNING EXERCISE. Not an after-flight record or flight authorization. No aircraft dispatched."
        )
        return JSONResponse(
            data, headers={"Content-Disposition": 'attachment; filename="planning-review.json"'}
        )

    @app.get("/")
    def index():
        """Serve only the fixed compiled index, never arbitrary filesystem paths."""
        if not (ROOT / "dist/index.html").is_file():
            raise HTTPException(503, "Build frontend with npm ci and npm run build")
        return FileResponse(ROOT / "dist/index.html")

    if (ROOT / "dist/assets").is_dir():
        app.mount("/assets", StaticFiles(directory=ROOT / "dist/assets"), name="assets")
    return app
