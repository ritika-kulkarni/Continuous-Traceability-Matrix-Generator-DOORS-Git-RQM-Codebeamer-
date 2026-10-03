"""IBM DOORS Next / DWA REST adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from traceability.adapters.http_base import HttpAdapterBase
from traceability.config import DoorsSettings
from traceability.domain.models import ArtifactSource, Requirement
from traceability.domain.requirement_tag import RequirementTagParser


class DoorsAdapter(HttpAdapterBase):
    """Fetches requirements from DOORS via a REST façade.

    Expected endpoint shape (configurable per deployment):
      GET /modules/{module}/requirements
      GET /requirements?tag=REQ_...
    """

    def __init__(
        self,
        settings: DoorsSettings,
        *,
        tag_parser: RequirementTagParser | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        auth = None
        if settings.username:
            auth = (settings.username, settings.password.get_secret_value())
        super().__init__(
            system="doors",
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            client=client,
            auth=auth,
            headers={"Accept": "application/json"},
        )
        self._module_path = settings.module_path
        self._tag_parser = tag_parser or RequirementTagParser()

    async def fetch_requirements(self) -> list[Requirement]:
        payload = await self.get_json(
            "/requirements",
            params={"module": self._module_path},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._to_requirement(item) for item in items]

    async def get_requirement_by_tag(self, tag: str) -> Requirement | None:
        normalized = self._tag_parser.normalize(tag)
        payload = await self.get_json("/requirements", params={"tag": normalized})
        items = payload if isinstance(payload, list) else payload.get("items", [])
        if not items:
            return None
        return self._to_requirement(items[0])

    def _to_requirement(self, item: dict[str, Any]) -> Requirement:
        raw_tag = item.get("tag") or item.get("id") or ""
        tags = self._tag_parser.extract(str(raw_tag))
        tag = tags[0] if tags else self._tag_parser.normalize(str(raw_tag))
        last_modified = item.get("lastModified") or item.get("last_modified")
        return Requirement(
            id=str(item.get("id") or tag),
            tag=tag,
            title=str(item.get("title") or item.get("name") or tag),
            description=str(item.get("description") or ""),
            source=ArtifactSource.DOORS,
            module=str(item.get("module") or self._module_path),
            status=str(item.get("status") or "Approved"),
            parent_id=str(item["parentId"]) if item.get("parentId") else None,
            attributes=dict(item.get("attributes") or {}),
            last_modified=datetime.fromisoformat(last_modified) if last_modified else None,
        )
