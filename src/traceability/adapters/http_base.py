"""Shared HTTP client utilities for ALM adapters."""

from __future__ import annotations

from typing import Any

import httpx

from traceability.exceptions import AdapterError, AuthenticationError, NotFoundError
from traceability.resilience import with_retries


class HttpAdapterBase:
    def __init__(
        self,
        *,
        system: str,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
        headers: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | None = None,
    ) -> None:
        self.system = system
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout_seconds,
            headers=headers or {},
            auth=auth,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> HttpAdapterBase:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        action: str | None = None,
    ) -> httpx.Response:
        async def _do() -> httpx.Response:
            response = await self._client.request(method, path, params=params, json=json)
            if response.status_code in {401, 403}:
                raise AuthenticationError(self.system, f"HTTP {response.status_code}")
            if response.status_code == 404:
                raise NotFoundError(self.system, path)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code in {408, 425, 429, 500, 502, 503, 504}
                raise AdapterError(
                    self.system,
                    f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
                    retryable=retryable,
                ) from exc
            return response

        return await with_retries(
            _do,
            system=self.system,
            max_attempts=self.max_retries,
            action=action or f"{method} {path}",
        )

    async def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        response = await self.request("GET", path, params=params)
        return response.json()
