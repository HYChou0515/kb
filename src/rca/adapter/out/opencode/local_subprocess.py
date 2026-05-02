"""LocalSubprocessOpencodeRuntime — opencode `serve` as a child process.

POC impl of IOpencodeRuntime: spawns `opencode serve` lazily on first
create_session, shuts it down at stop(). Talks to the running server's
HTTP API for session lifecycle (create / delete / inspect).

opencode's `serve` permanently anchors its project root to the cwd of
the launched process — `POST /session` ignores `directory` / `cwd` /
`path` body fields. So we must (re)start opencode with the workspace
directory as cwd whenever a session for a different workspace is opened.

XDG isolation: child opencode uses XDG_DATA_HOME=<opencode_data_root> so
its SQLite + snapshots live under our control (per-deployment), not in
the host user's ~/.local/share/opencode. Same for XDG_CONFIG_HOME, which
gets the workspace-config-disabled flag in env so the agent cannot reach
its own config via a file.

For prod (k8s), swap to RemoteOpencodeRuntime: same IOpencodeRuntime
interface, no subprocess management — just an httpx client pointing at
the opencode-deployment service URL.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import os
import signal
from pathlib import Path
from typing import Any

import httpx

from rca.ports.out.opencode_runtime import IOpencodeRuntime

logger = logging.getLogger(__name__)


_HEALTH_PATH = "/global/health"
_SESSION_PATH = "/session"
_STARTUP_TIMEOUT_SECONDS = 15.0
_STARTUP_POLL_INTERVAL = 0.2


class LocalSubprocessOpencodeRuntime(IOpencodeRuntime):
    def __init__(
        self,
        *,
        port: int = 4096,
        host: str = "127.0.0.1",
        opencode_data_root: Path,
        config_content: dict[str, Any],
        server_password: str = "",
        openchamber_base_url: str = "",
    ) -> None:
        self._port = port
        self._host = host
        self._opencode_data_root = opencode_data_root
        self._config_content = config_content
        self._server_password = server_password
        # When non-empty, session_url() points at OpenChamber instead of
        # opencode's built-in /app. OpenChamber must be run separately and
        # configured via OPENCODE_SKIP_START=true to attach to this same
        # opencode server.
        self._openchamber_base_url = openchamber_base_url.rstrip("/")
        self._proc: asyncio.subprocess.Process | None = None
        self._client: httpx.AsyncClient | None = None
        self._cwd: Path | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    # ─── lifecycle ─────────────────────────────────────────────────────────

    async def start(self, *, cwd: Path) -> None:
        """Spawn opencode serve in `cwd`, wait for /global/health to respond.

        `cwd` becomes opencode's project root for every session this process
        ever creates — opencode resolves the project once at startup from its
        own cwd and ignores per-request directory hints.
        """
        self._opencode_data_root.mkdir(parents=True, exist_ok=True)
        cwd.mkdir(parents=True, exist_ok=True)

        env = {
            **os.environ,
            "XDG_DATA_HOME": str(self._opencode_data_root),
            "XDG_CONFIG_HOME": str(self._opencode_data_root / "config"),
            "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
            "OPENCODE_CONFIG_CONTENT": json.dumps(self._config_content),
        }
        if self._server_password:
            env["OPENCODE_SERVER_PASSWORD"] = self._server_password

        logger.info(
            "spawning opencode serve port=%d cwd=%s data_root=%s",
            self._port,
            cwd,
            self._opencode_data_root,
        )
        self._proc = await asyncio.create_subprocess_exec(
            "opencode",
            "serve",
            f"--port={self._port}",
            f"--hostname={self._host}",
            env=env,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._cwd = cwd

        # Build the HTTP client now (so health-poll can use it).
        auth = None
        if self._server_password:
            auth = httpx.BasicAuth("opencode", self._server_password)
        self._client = httpx.AsyncClient(
            base_url=self.base_url, auth=auth, timeout=10.0
        )

        await self._wait_until_healthy()

    async def stop(self, *, grace_seconds: int = 5) -> None:
        """SIGTERM, wait, escalate to SIGKILL if needed."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        try:
            if self._proc is None or self._proc.returncode is not None:
                return
            try:
                self._proc.send_signal(signal.SIGTERM)
                await asyncio.wait_for(self._proc.wait(), timeout=grace_seconds)
            except asyncio.TimeoutError:
                logger.warning("opencode did not exit on SIGTERM, sending SIGKILL")
                self._proc.kill()
                await self._proc.wait()
        finally:
            self._proc = None
            self._cwd = None

    async def _ensure_running_for(self, cwd: Path) -> None:
        """Make sure opencode serve is up and anchored to `cwd`.

        Restart strategy: opencode's project root is fixed at process
        startup, so a session for a different workspace requires a full
        process bounce. POC scope assumes one active workspace at a time;
        cross-workspace concurrency would need a runtime-per-case design.
        """
        target = cwd.resolve()
        if (
            self._proc is not None
            and self._proc.returncode is None
            and self._cwd is not None
            and self._cwd.resolve() == target
        ):
            return
        if self._proc is not None:
            logger.info(
                "restarting opencode serve to switch project root: %s → %s",
                self._cwd,
                target,
            )
            await self.stop()
        await self.start(cwd=target)

    async def _wait_until_healthy(self) -> None:
        deadline = asyncio.get_event_loop().time() + _STARTUP_TIMEOUT_SECONDS
        while asyncio.get_event_loop().time() < deadline:
            try:
                if await self.health_check():
                    return
            except Exception:
                pass
            await asyncio.sleep(_STARTUP_POLL_INTERVAL)
        # Timed out — drain stderr for diagnosis and raise.
        stderr = b""
        if self._proc and self._proc.stderr:
            try:
                stderr = await asyncio.wait_for(self._proc.stderr.read(2048), 0.5)
            except asyncio.TimeoutError:
                pass
        raise RuntimeError(
            f"opencode serve failed to become healthy within "
            f"{_STARTUP_TIMEOUT_SECONDS}s. stderr (truncated): {stderr.decode(errors='replace')[:2048]}"
        )

    # ─── IOpencodeRuntime ─────────────────────────────────────────────────

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            r = await self._client.get(_HEALTH_PATH)
        except httpx.RequestError:
            return False
        return r.status_code < 300

    async def create_session(self, *, directory: Path) -> str:
        # opencode anchors its project root to the cwd of `opencode serve`
        # and ignores per-request directory hints, so we (re)start the server
        # in `directory` before asking for the session.
        await self._ensure_running_for(directory)
        client = self._require_client()
        r = await client.post(_SESSION_PATH, json={})
        r.raise_for_status()
        body = r.json()
        sess_id = body.get("id") or body.get("sessionID") or body.get("session_id")
        if not sess_id:
            raise RuntimeError(
                f"opencode POST /session returned no recognizable session id: {body!r}"
            )
        return sess_id

    async def delete_session(self, opencode_session_id: str) -> None:
        client = self._require_client()
        # 404 is treated as success — the session is already gone, which is
        # what we wanted.
        r = await client.delete(f"{_SESSION_PATH}/{opencode_session_id}")
        if r.status_code not in (200, 204, 404):
            r.raise_for_status()

    async def last_message_at(self, opencode_session_id: str) -> dt.datetime | None:
        client = self._require_client()
        try:
            r = await client.get(f"{_SESSION_PATH}/{opencode_session_id}/message")
        except httpx.RequestError as exc:
            logger.debug("last_message_at: request failed: %s", exc)
            return None
        if r.status_code == 404:
            return None
        if r.status_code >= 300:
            return None
        messages = r.json()
        if not messages or not isinstance(messages, list):
            return None
        # Each message has a created/timestamp field. opencode's exact field
        # name varies by version — try common candidates and fall back to
        # `time` / `createdAt` / numeric `created`.
        last = messages[-1]
        ts = (
            last.get("created")
            or last.get("createdAt")
            or last.get("time")
            or last.get("timestamp")
        )
        if ts is None:
            return None
        return _parse_timestamp(ts)

    def session_url(self, opencode_session_id: str) -> str:
        # opencode's built-in UI is at /app; OpenChamber serves the same
        # session at /. Both accept ?session=<id>. We hand back OpenChamber's
        # URL when configured because its file tree, diff viewer, and approval
        # UX are production-grade — opencode's /app is dev-tooling.
        if self._openchamber_base_url:
            return f"{self._openchamber_base_url}/?session={opencode_session_id}"
        return f"{self.base_url}/app?session={opencode_session_id}"

    # ─── helpers ───────────────────────────────────────────────────────────

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "LocalSubprocessOpencodeRuntime not started — call start() first"
            )
        return self._client


def _parse_timestamp(raw: Any) -> dt.datetime | None:
    """opencode timestamps come as either ISO string or numeric epoch (ms or s).
    Be defensive — None on parse failure rather than raising in the watchdog
    hot path."""
    if isinstance(raw, str):
        try:
            return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(raw, (int, float)):
        # Heuristic: > 10^12 means milliseconds since epoch, else seconds
        seconds = raw / 1000.0 if raw > 1e12 else float(raw)
        try:
            return dt.datetime.fromtimestamp(seconds, tz=dt.UTC)
        except (ValueError, OSError):
            return None
    return None
