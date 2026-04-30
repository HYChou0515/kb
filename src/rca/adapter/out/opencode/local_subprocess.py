"""LocalSubprocessOpencodeRuntime — opencode `serve` as a child process.

POC impl of IOpencodeRuntime: spawns one `opencode serve` subprocess at
start(), shuts it down at stop(). Talks to the running server's HTTP API
for session lifecycle (create / delete / inspect).

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
    ) -> None:
        self._port = port
        self._host = host
        self._opencode_data_root = opencode_data_root
        self._config_content = config_content
        self._server_password = server_password
        self._proc: asyncio.subprocess.Process | None = None
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    # ─── lifecycle ─────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Spawn opencode serve, wait for /global/health to respond 2xx."""
        self._opencode_data_root.mkdir(parents=True, exist_ok=True)

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
            "spawning opencode serve port=%d data_root=%s",
            self._port,
            self._opencode_data_root,
        )
        self._proc = await asyncio.create_subprocess_exec(
            "opencode",
            "serve",
            f"--port={self._port}",
            f"--hostname={self._host}",
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

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
        client = self._require_client()
        # opencode's POST /session accepts a directory pin in the body —
        # the session is scoped to operate within that workspace dir.
        r = await client.post(
            _SESSION_PATH,
            json={"directory": str(directory)},
        )
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
        # opencode's web UI is at /app and accepts session via query.
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
