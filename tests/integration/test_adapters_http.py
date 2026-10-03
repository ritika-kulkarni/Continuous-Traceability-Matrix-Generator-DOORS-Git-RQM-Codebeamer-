from datetime import UTC, datetime

import httpx
import pytest
import respx

from traceability.adapters.codebeamer import CodebeamerAdapter
from traceability.adapters.doors import DoorsAdapter
from traceability.adapters.git_client import GitAdapter
from traceability.adapters.rqm import RqmAdapter
from traceability.config import CodebeamerSettings, DoorsSettings, GitSettings, RqmSettings


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_doors_adapter_fetches_and_maps_requirements() -> None:
    route = respx.get("https://doors.test/api/requirements").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "D-100",
                        "tag": "REQ_ADAS_USS_042",
                        "title": "USS detect",
                        "status": "Approved",
                        "module": "/ADAS/USS",
                        "lastModified": "2026-03-01T10:00:00+00:00",
                    }
                ]
            },
        )
    )
    settings = DoorsSettings(
        base_url="https://doors.test/api",
        username="u",
        password="p",
        max_retries=1,
    )
    async with DoorsAdapter(settings) as adapter:
        reqs = await adapter.fetch_requirements()
    assert route.called
    assert len(reqs) == 1
    assert reqs[0].tag == "REQ_ADAS_USS_042"
    assert reqs[0].last_modified == datetime(2026, 3, 1, 10, 0, tzinfo=UTC)


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_git_adapter_extracts_pr_tags() -> None:
    respx.get("https://api.github.com/repos/org/ecu/pulls/42").mock(
        return_value=httpx.Response(
            200,
            json={
                "number": 42,
                "title": "feat REQ_ADAS_USS_042",
                "body": "desc",
                "user": {"login": "dev"},
                "head": {"ref": "feature", "sha": "abc"},
                "base": {"ref": "main"},
                "html_url": "https://example.com/pr/42",
            },
        )
    )
    respx.get("https://api.github.com/repos/org/ecu/pulls/42/commits").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "sha": "abc",
                    "commit": {
                        "message": "Requires: REQ_ADAS_USS_042",
                        "author": {"name": "dev", "date": "2026-03-01T00:00:00Z"},
                    },
                }
            ],
        )
    )
    settings = GitSettings(
        base_url="https://api.github.com",
        owner="org",
        repo="ecu",
        token="t",
        max_retries=1,
    )
    async with GitAdapter(settings) as adapter:
        pr = await adapter.fetch_pull_request(42)
    assert pr.number == 42
    assert pr.commits[0].requirement_tags == ("REQ_ADAS_USS_042",)


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_codebeamer_and_rqm_adapters() -> None:
    respx.get("https://cb.test/cb/rest/projects/1000/items").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "CB-1",
                        "name": "Design",
                        "type": "Design",
                        "requirementTags": ["REQ_ADAS_USS_042"],
                    }
                ]
            },
        )
    )
    respx.get("https://rqm.test/resources/testcases").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "TC-1",
                        "name": "unit case",
                        "level": "unit",
                        "requirementTags": ["REQ_ADAS_USS_042"],
                    }
                ]
            },
        )
    )
    respx.get("https://rqm.test/resources/executions").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "EX-1",
                        "testCaseId": "TC-1",
                        "status": "passed",
                        "executedAt": "2026-03-02T00:00:00Z",
                        "buildId": "b1",
                    }
                ]
            },
        )
    )

    cb = CodebeamerAdapter(
        CodebeamerSettings(base_url="https://cb.test/cb/rest", token="t", max_retries=1)
    )
    rqm = RqmAdapter(
        RqmSettings(base_url="https://rqm.test", username="u", password="p", max_retries=1)
    )
    try:
        items = await cb.fetch_items()
        cases = await rqm.fetch_test_cases_for_requirement("REQ_ADAS_USS_042")
        executions = await rqm.fetch_executions(build_id="b1")
    finally:
        await cb.aclose()
        await rqm.aclose()

    assert items[0].requirement_tags == ("REQ_ADAS_USS_042",)
    assert cases[0].id == "TC-1"
    assert executions[0].status.value == "passed"


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_adapter_retries_on_503_then_succeeds() -> None:
    route = respx.get("https://doors.test/api/requirements").mock(
        side_effect=[
            httpx.Response(503, text="busy"),
            httpx.Response(200, json={"items": []}),
        ]
    )
    settings = DoorsSettings(base_url="https://doors.test/api", max_retries=3)
    async with DoorsAdapter(settings) as adapter:
        reqs = await adapter.fetch_requirements()
    assert reqs == []
    assert route.call_count == 2
