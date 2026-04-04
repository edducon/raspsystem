from __future__ import annotations

import json
import threading
import time
import socket
from urllib import error, parse, request

from app.core.config import settings


class RaspyxService:
    _cached_access_token: str | None = None
    _response_cache: dict[str, tuple[float, object]] = {}
    _endpoint_locks: dict[str, threading.Lock] = {}
    _endpoint_locks_guard = threading.Lock()
    _cache_ttl_seconds = 30 * 60

    def _load_json(self, url: str, *, method: str = "GET", payload: dict | None = None, retry_count: int = 1) -> object:
        headers = {"Accept": "application/json"}
        data_bytes = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(payload).encode("utf-8")

        if url != settings.raspyx_auth_url:
            headers["Authorization"] = f"Bearer {self.get_access_token()}"

        req = request.Request(url=url, method=method, data=data_bytes, headers=headers)

        try:
            with request.urlopen(req, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code == 401 and url != settings.raspyx_auth_url and retry_count > 0:
                self.__class__._cached_access_token = None
                return self._load_json(url, method=method, payload=payload, retry_count=retry_count - 1)

            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Raspyx request failed with {exc.code}: {detail}") from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            print(f"[RaspyxService] API Connection Error / Timeout: {exc}")
            return {"success": False, "result": [], "response": []}

    def _cached_get(self, endpoint: str) -> object:
        cached = self.__class__._response_cache.get(endpoint)
        now = time.time()
        if cached is not None and cached[0] > now:
            return cached[1]

        endpoint_lock = self._endpoint_lock(endpoint)
        with endpoint_lock:
            cached = self.__class__._response_cache.get(endpoint)
            now = time.time()
            if cached is not None and cached[0] > now:
                return cached[1]

            payload = self._load_json(f"{settings.raspyx_api_base_url}{endpoint}")
            self.__class__._response_cache[endpoint] = (now + self._cache_ttl_seconds, payload)
            return payload

    @classmethod
    def _endpoint_lock(cls, endpoint: str) -> threading.Lock:
        with cls._endpoint_locks_guard:
            lock = cls._endpoint_locks.get(endpoint)
            if lock is None:
                lock = threading.Lock()
                cls._endpoint_locks[endpoint] = lock
            return lock

    def get_access_token(self) -> str:
        if self.__class__._cached_access_token is not None:
            return self.__class__._cached_access_token

        try:
            payload = self._load_json(
                settings.raspyx_auth_url,
                method="POST",
                payload={
                    "username": settings.raspyx_username,
                    "password": settings.raspyx_password,
                },
            )
        except Exception:
            return "offline_mock_token"

        token = None
        if isinstance(payload, dict):
            if payload.get("success") and isinstance(payload.get("result"), dict):
                token = payload["result"].get("access_token")
            elif payload.get("status") == "OK" and isinstance(payload.get("response"), dict):
                token = payload["response"].get("token")

        if not token:
            print("Raspyx auth did not return an access token, using offline mode.")
            return "offline_mock_token"

        self.__class__._cached_access_token = str(token)
        return self.__class__._cached_access_token

    def get_groups(self) -> object:
        return self._cached_get("/groups")

    def get_subjects(self) -> object:
        return self._cached_get("/subjects")

    def get_teachers(self) -> object:
        """GET /v2/teachers — список всех преподавателей {uuid, full_name}."""
        return self._cached_get("/teachers")

    def get_group_schedule(self, group_number: str, *, is_session: bool = False) -> object:
        encoded = parse.quote(group_number)
        return self._cached_get(f"/schedule/group_number/{encoded}?is_session={str(is_session).lower()}")

    def get_teacher_schedule(self, teacher_full_name: str, *, is_session: bool = False) -> object:
        encoded = parse.quote(teacher_full_name)
        return self._cached_get(f"/schedule/teacher_fio/{encoded}?is_session={str(is_session).lower()}")
