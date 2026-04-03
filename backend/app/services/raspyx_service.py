from __future__ import annotations

import json
import time
from urllib import error, parse, request

from app.core.config import settings


class RaspyxService:
    _cached_access_token: str | None = None
    _response_cache: dict[str, tuple[float, object]] = {}
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

    def _cached_get(self, endpoint: str) -> object:
        cached = self.__class__._response_cache.get(endpoint)
        now = time.time()
        if cached is not None and cached[0] > now:
            return cached[1]

        payload = self._load_json(f"{settings.raspyx_api_base_url}{endpoint}")
        self.__class__._response_cache[endpoint] = (now + self._cache_ttl_seconds, payload)
        return payload

    def get_access_token(self) -> str:
        if self.__class__._cached_access_token is not None:
            return self.__class__._cached_access_token

        payload = self._load_json(
            settings.raspyx_auth_url,
            method="POST",
            payload={
                "username": settings.raspyx_username,
                "password": settings.raspyx_password,
            },
        )

        token = None
        if isinstance(payload, dict):
            if payload.get("success") and isinstance(payload.get("result"), dict):
                token = payload["result"].get("access_token")
            elif payload.get("status") == "OK" and isinstance(payload.get("response"), dict):
                token = payload["response"].get("token")

        if not token:
            raise RuntimeError("Raspyx auth did not return an access token")

        self.__class__._cached_access_token = str(token)
        return self.__class__._cached_access_token

    def get_groups(self) -> object:
        return self._cached_get("/groups")

    def get_subjects(self) -> object:
        return self._cached_get("/subjects")

    def get_group_schedule(self, group_number: str, *, is_session: bool = False) -> object:
        encoded = parse.quote(group_number)
        return self._cached_get(f"/schedule/group_number/{encoded}?is_session={str(is_session).lower()}")

    def get_teacher_schedule(self, teacher_full_name: str, *, is_session: bool = False) -> object:
        encoded = parse.quote(teacher_full_name)
        return self._cached_get(f"/schedule/teacher_fio/{encoded}?is_session={str(is_session).lower()}")
