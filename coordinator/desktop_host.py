"""Jason Stys: owned prebound local service with readiness and completion-based shutdown. Lines: docs/SOURCE_MAP.md.

Host and OwnedServer retain the original authenticated application; no public setup,
remote quit route, server reuse, aircraft endpoint or account bypass is introduced.
"""

import json
import os
import secrets
import socket
import threading

import uvicorn

from coordinator.api import create_app


class OwnedServer(uvicorn.Server):
    """Announce only actual successful startup; the owner window controls this exact server object."""

    def __init__(self, config, ready, record):
        """Hold an in-process readiness event and public-only package/nonce identity."""
        super().__init__(config)
        self.ready = ready
        self.record = record

    async def startup(self, sockets=None):
        """Use pinned Uvicorn's real startup before emitting the only machine readiness marker."""
        await super().startup(sockets=sockets)
        if not self.started:
            raise RuntimeError("Application startup did not complete")
        print("PORTFOLIO_READY " + json.dumps(self.record), flush=True)
        self.ready.set()


class Host:
    """One owned ephemeral listener and application thread; never adopt an existing user's service."""

    def __init__(self, profile, metadata):
        """Bind loopback before deriving the exact trusted origin and leave domain authorization intact."""
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(16)
        self.port = self.listener.getsockname()[1]
        self.origin = f"http://127.0.0.1:{self.port}"
        self.ready = threading.Event()
        self.error = None
        self.record = {
            "url": self.origin + "/",
            "package": metadata,
            "instance": os.environ.get("PORTABLE_SMOKE_NONCE", secrets.token_hex(16)),
        }
        try:
            app = create_app(profile.store.path, self.origin, cookie_name=profile.cookie_name)
            app.state.desktop_identity = self.record
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=0,
                access_log=False,
                log_config=None,
                loop="asyncio",
                http="h11",
                ws="none",
                lifespan="on",
                proxy_headers=False,
                limit_concurrency=16,
                timeout_graceful_shutdown=None,
            )
            self.server = OwnedServer(config, self.ready, self.record)
            self.thread = threading.Thread(target=self._run, name="owned-workspace-service")
        except BaseException:
            self.listener.close()
            raise

    def _run(self):
        """Retain startup/runtime failure for the owner; close only this listener when the service finishes."""
        try:
            self.server.run(sockets=[self.listener])
        except Exception as error:
            self.error = error
        except (KeyboardInterrupt, SystemExit) as error:
            self.error = RuntimeError("Owned service interrupted before normal completion")
            self.error.__cause__ = error
        finally:
            self.listener.close()
            self.ready.set()

    def start(self, timeout=10):
        """Wait for actual owned startup, with a deadline instead of sleeps or a liveness-only substitute."""
        self.thread.start()
        if not self.ready.wait(timeout) or self.error or not self.server.started:
            self.server.should_exit = True
            self.thread.join(timeout=timeout)
            raise RuntimeError("Owned service did not become ready") from self.error

    def stop(self, timeout=20):
        """Drain real requests without cancellation/forced exit; a busy service keeps its owner window open."""
        self.server.should_exit = True
        if self.thread.ident is None:
            self.listener.close()
            return
        self.thread.join(timeout=timeout)
        if self.thread.is_alive():
            raise RuntimeError("Still draining active work; wait and choose Quit again")
        if self.error:
            raise RuntimeError("Owned service exited with an error") from self.error
