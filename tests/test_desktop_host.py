"""Jason Stys: actual owned Uvicorn auth/readiness and held-request completion without cancellation. Lines: docs/SOURCE_MAP.md."""

import http.client
import json
import socket
import threading

import httpx
import pytest

from coordinator.desktop_host import Host
from coordinator.desktop_profile import FIRST_ROLE, PRODUCT, Profile


def prepared(tmp_path):
    """Provision only a new synthetic profile using the same native-owner account contract."""
    profile = Profile(tmp_path / "profile")
    profile.create_account(
        "owner", "Synthetic-native-only-2026!", "Synthetic-native-only-2026!", FIRST_ROLE
    )
    return profile


def request(host, path, *, method="GET", body=None, headers=None):
    """Fixed owned loopback only; no proxy, external fetch, source-service fallback or redirects."""
    connection = http.client.HTTPConnection("127.0.0.1", host.port, timeout=8)
    try:
        connection.request(
            method, path, body=json.dumps(body) if body is not None else None, headers=headers or {}
        )
        response = connection.getresponse()
        return response.status, response.read(), dict(response.getheaders())
    finally:
        connection.close()


def test_actual_readiness_private_login_and_owned_stop(tmp_path):
    """Actual API sessions/CSRF stay authoritative, and native completion closes only the owned listener."""
    profile = prepared(tmp_path)
    metadata = {"name": PRODUCT, "version": "0.2.0", "mode": "development"}
    host = Host(profile, metadata)
    try:
        host.start()
        code, raw, _ = request(host, "/healthz")
        health = json.loads(raw)
        assert code == 200 and health["desktop"] == host.record
        assert health["desktop"]["package"] == metadata and str(tmp_path) not in raw.decode()
        assert request(host, "/api/workspace")[0] == 401
        assert request(host, "/healthz", headers={"Host": "foreign.invalid"})[0] == 400
        login = {"username": "owner", "password": "Synthetic-native-only-2026!"}
        assert (
            request(
                host,
                "/api/login",
                method="POST",
                body=login,
                headers={"Origin": "http://foreign.invalid", "Content-Type": "application/json"},
            )[0]
            == 403
        )
        code, raw, headers = request(
            host,
            "/api/login",
            method="POST",
            body=login,
            headers={"Origin": host.origin, "Content-Type": "application/json"},
        )
        assert code == 200 and json.loads(raw)["role"] == FIRST_ROLE
        cookie = headers["set-cookie"].split(";", 1)[0]
        assert request(host, "/api/workspace", headers={"Cookie": cookie})[0] == 200
        assert request(
            host,
            "/api/desktop/setup",
            method="POST",
            body=login,
            headers={"Origin": host.origin, "Content-Type": "application/json"},
        )[0] in {401, 404}
        host.stop()
        assert not host.thread.is_alive() and host.listener.fileno() == -1
        with pytest.raises(OSError):
            request(host, "/healthz")
        assert profile.count_users() == 1
    finally:
        if host.thread.is_alive():
            host.stop()
        profile.close()


def test_actual_partial_body_bounds_pre_shutdown_drain(tmp_path):
    """A real held HTTP request reaches ASGI receive, then times out before the owner reports completion."""
    profile = prepared(tmp_path)
    host = Host(profile, {"name": PRODUCT, "version": "0.2.0", "mode": "development"})
    received = threading.Event()

    class ObserveRead:
        """Observe actual received bytes without replacing application validation, body timeout or response."""

        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            async def observed():
                message = await receive()
                if message.get("body") and message.get("more_body"):
                    received.set()
                return message

            await self.app(scope, observed, send)

    host.server.config.app.add_middleware(ObserveRead)
    try:
        host.start()
        with socket.create_connection(("127.0.0.1", host.port), timeout=8) as connection:
            connection.sendall(
                (
                    f"POST /api/login HTTP/1.1\r\nHost: 127.0.0.1:{host.port}\r\nOrigin: {host.origin}\r\nContent-Type: application/json\r\nContent-Length: 200\r\nConnection: close\r\n\r\n"
                    + "{"
                ).encode()
            )
            assert received.wait(3), "actual partial request never reached ASGI"
            with pytest.raises(RuntimeError, match="Still draining"):
                host.stop(timeout=0.01)
            assert host.thread.is_alive()
            response = http.client.HTTPResponse(connection)
            response.begin()
            assert (
                response.status == 408 and json.loads(response.read())["detail"] == "Body timeout"
            )
            host.stop(timeout=10)
        assert not host.thread.is_alive() and profile.count_users() == 1
    finally:
        if host.thread.is_alive():
            host.stop()
        profile.close()


def test_startup_failure_is_never_reported_as_ready(tmp_path, monkeypatch):
    """A real owned thread captures the failing server and closes its own listener without adoption."""
    profile = prepared(tmp_path)
    host = Host(profile, {})

    def broken(*_args, **_kwargs):
        raise RuntimeError("synthetic startup failure")

    monkeypatch.setattr(host.server, "run", broken)
    try:
        with pytest.raises(RuntimeError, match="did not become ready"):
            host.start()
        assert not host.server.started and host.listener.fileno() == -1
        with pytest.raises(RuntimeError, match="exited with an error"):
            host.stop()
    finally:
        profile.close()


def test_two_actual_profiles_keep_sessions_in_one_host_scoped_cookie_jar(tmp_path):
    """Real different-port services must not overwrite cookies or accept another profile's session/CSRF."""
    first = Profile(tmp_path / "alpha")
    second = Profile(tmp_path / "bravo")
    password = "Synthetic-native-only-2026!"
    first.create_account("alpha", password, password, FIRST_ROLE)
    second.create_account("bravo", password, password, FIRST_ROLE)
    assert first.cookie_name != second.cookie_name
    hosts = [Host(first, {}), Host(second, {})]
    try:
        for host in hosts:
            host.start()
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=6) as client:
            for host, name in zip(hosts, ("alpha", "bravo"), strict=True):
                response = client.post(
                    host.origin + "/api/login",
                    headers={"Origin": host.origin},
                    json={"username": name, "password": password},
                )
                assert response.status_code == 200
            assert {cookie.name for cookie in client.cookies.jar} == {
                first.cookie_name,
                second.cookie_name,
            }
            users = [client.get(host.origin + "/api/me").json() for host in hosts]
            assert [user["name"] for user in users] == ["alpha", "bravo"]
            foreign_cookie = first.cookie_name + "=" + client.cookies.get(first.cookie_name)
            assert (
                client.get(
                    hosts[1].origin + "/api/me", headers={"Cookie": foreign_cookie}
                ).status_code
                == 401
            )
            wrong_csrf = client.post(
                hosts[1].origin + "/api/logout",
                headers={"Origin": hosts[1].origin, "X-CSRF-Token": users[0]["csrf"]},
                json={},
            )
            assert wrong_csrf.status_code == 403
            assert (
                client.post(
                    hosts[0].origin + "/api/logout",
                    headers={"Origin": hosts[0].origin, "X-CSRF-Token": users[0]["csrf"]},
                    json={},
                ).status_code
                == 200
            )
            assert client.get(hosts[0].origin + "/api/me").status_code == 401
            assert client.get(hosts[1].origin + "/api/me").json()["name"] == "bravo"
    finally:
        for host in hosts:
            host.stop()
        first.close()
        second.close()


@pytest.mark.parametrize("invalid", ["", "x\r\nInjected: value", "cookie; unsafe", "x" * 65, None])
def test_invalid_cookie_namespace_is_rejected_before_database_creation(tmp_path, invalid):
    """Trusted native configuration still cannot create malformed cookie headers or initialize a DB on failure."""
    from coordinator.api import create_app

    database = tmp_path / "never-created.sqlite3"
    with pytest.raises(ValueError, match="namespace"):
        create_app(database, cookie_name=invalid)
    assert not database.exists()
