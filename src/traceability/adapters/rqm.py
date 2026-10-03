"""IBM Engineering Test Management (RQM) REST adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from traceability.adapters.http_base import HttpAdapterBase
from traceability.config import RqmSettings
from traceability.domain.models import ExecutionStatus, RqmExecution, RqmTestCase, VerificationLevel
from traceability.domain.requirement_tag import RequirementTagParser

_STATUS_MAP = {
    "passed": ExecutionStatus.PASSED,
    "pass": ExecutionStatus.PASSED,
    "failed": ExecutionStatus.FAILED,
    "fail": ExecutionStatus.FAILED,
    "blocked": ExecutionStatus.BLOCKED,
    "not_run": ExecutionStatus.NOT_RUN,
    "notrun": ExecutionStatus.NOT_RUN,
    "inconclusive": ExecutionStatus.INCONCLUSIVE,
}

_LEVEL_MAP = {
    "unit": VerificationLevel.UNIT,
    "integration": VerificationLevel.INTEGRATION,
    "system": VerificationLevel.SYSTEM,
    "acceptance": VerificationLevel.ACCEPTANCE,
}


class RqmAdapter(HttpAdapterBase):
    def __init__(
        self,
        settings: RqmSettings,
        *,
        tag_parser: RequirementTagParser | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        auth = None
        if settings.username:
            auth = (settings.username, settings.password.get_secret_value())
        super().__init__(
            system="rqm",
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            client=client,
            auth=auth,
            headers={"Accept": "application/json"},
        )
        self._project_area = settings.project_area
        self._tag_parser = tag_parser or RequirementTagParser()

    async def fetch_test_cases(self) -> list[RqmTestCase]:
        payload = await self.get_json(
            "/resources/testcases",
            params={"projectArea": self._project_area},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._to_test_case(item) for item in items]

    async def fetch_test_cases_for_requirement(self, requirement_tag: str) -> list[RqmTestCase]:
        tag = self._tag_parser.normalize(requirement_tag)
        payload = await self.get_json(
            "/resources/testcases",
            params={"projectArea": self._project_area, "requirementTag": tag},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        cases = [self._to_test_case(item) for item in items]
        # Defensive filter when server-side filtering is unavailable
        return [c for c in cases if tag in c.requirement_tags]

    async def fetch_executions(
        self,
        *,
        test_case_id: str | None = None,
        build_id: str | None = None,
    ) -> list[RqmExecution]:
        params: dict[str, Any] = {"projectArea": self._project_area}
        if test_case_id:
            params["testCaseId"] = test_case_id
        if build_id:
            params["buildId"] = build_id
        payload = await self.get_json("/resources/executions", params=params)
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._to_execution(item) for item in items]

    def _to_test_case(self, item: dict[str, Any]) -> RqmTestCase:
        tags = self._tag_parser.extract(
            " ".join(
                [
                    str(item.get("name") or ""),
                    str(item.get("description") or ""),
                    " ".join(str(t) for t in (item.get("requirementTags") or [])),
                ]
            )
        )
        level_raw = str(item.get("level") or item.get("testLevel") or "unit").lower()
        return RqmTestCase(
            id=str(item["id"]),
            name=str(item.get("name") or item["id"]),
            level=_LEVEL_MAP.get(level_raw, VerificationLevel.UNIT),
            requirement_tags=tags,
            script_path=item.get("scriptPath"),
        )

    def _to_execution(self, item: dict[str, Any]) -> RqmExecution:
        status_raw = str(item.get("status") or "not_run").lower().replace(" ", "_")
        executed = item.get("executedAt") or item.get("endTime")
        return RqmExecution(
            id=str(item["id"]),
            test_case_id=str(item.get("testCaseId") or item.get("testcaseId") or ""),
            status=_STATUS_MAP.get(status_raw, ExecutionStatus.NOT_RUN),
            executed_at=(
                datetime.fromisoformat(str(executed).replace("Z", "+00:00"))
                if executed
                else datetime.fromtimestamp(0)
            ),
            build_id=item.get("buildId"),
            requirement_tags=self._tag_parser.extract(
                " ".join(str(t) for t in (item.get("requirementTags") or []))
            ),
            log_url=item.get("logUrl"),
        )
