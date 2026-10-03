"""Codebeamer REST adapter for design / work items."""

from __future__ import annotations

from typing import Any

import httpx

from traceability.adapters.http_base import HttpAdapterBase
from traceability.config import CodebeamerSettings
from traceability.domain.models import CodeItem
from traceability.domain.requirement_tag import RequirementTagParser


class CodebeamerAdapter(HttpAdapterBase):
    def __init__(
        self,
        settings: CodebeamerSettings,
        *,
        tag_parser: RequirementTagParser | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        token = settings.token.get_secret_value()
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        super().__init__(
            system="codebeamer",
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            client=client,
            headers=headers,
        )
        self._project_id = settings.project_id
        self._tag_parser = tag_parser or RequirementTagParser()

    async def fetch_items(self) -> list[CodeItem]:
        payload = await self.get_json(
            f"/projects/{self._project_id}/items",
            params={"pageSize": 500},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._to_item(item) for item in items]

    async def fetch_items_for_requirement(self, requirement_tag: str) -> list[CodeItem]:
        tag = self._tag_parser.normalize(requirement_tag)
        payload = await self.get_json(
            f"/projects/{self._project_id}/items",
            params={"requirementTag": tag},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._to_item(item) for item in items]

    def _to_item(self, item: dict[str, Any]) -> CodeItem:
        text_blob = " ".join(
            str(item.get(key) or "")
            for key in ("title", "description", "requirementTags", "references")
        )
        tags = self._tag_parser.extract(text_blob)
        if item.get("requirementTags"):
            tags = tuple(
                sorted(
                    set(tags)
                    | {
                        self._tag_parser.normalize(t)
                        for t in item["requirementTags"]
                        if self._tag_parser.is_valid(str(t))
                    }
                )
            )
        req_ids = tuple(str(x) for x in (item.get("requirementIds") or []))
        return CodeItem(
            id=str(item["id"]),
            title=str(item.get("name") or item.get("title") or item["id"]),
            item_type=str(item.get("type") or item.get("trackerType") or "WorkItem"),
            requirement_ids=req_ids,
            requirement_tags=tags,
            url=item.get("uri") or item.get("url"),
            status=str(item.get("status") or "In Progress"),
        )
