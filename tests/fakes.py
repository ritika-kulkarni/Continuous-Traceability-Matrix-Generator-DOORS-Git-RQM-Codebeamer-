"""Reusable fake adapters for unit/integration tests."""

from __future__ import annotations

from traceability.domain.models import (
    CodeItem,
    GitCommit,
    PullRequest,
    Requirement,
    RqmExecution,
    RqmTestCase,
)


class FakeDoors:
    def __init__(self, requirements: list[Requirement]) -> None:
        self._by_tag = {r.tag: r for r in requirements}

    async def fetch_requirements(self) -> list[Requirement]:
        return list(self._by_tag.values())

    async def get_requirement_by_tag(self, tag: str) -> Requirement | None:
        return self._by_tag.get(tag.upper())


class FakeCodebeamer:
    def __init__(self, items: list[CodeItem]) -> None:
        self._items = items

    async def fetch_items(self) -> list[CodeItem]:
        return list(self._items)

    async def fetch_items_for_requirement(self, requirement_tag: str) -> list[CodeItem]:
        tag = requirement_tag.upper()
        return [i for i in self._items if tag in i.requirement_tags]


class FakeGit:
    def __init__(self, commits: list[GitCommit], pr: PullRequest | None = None) -> None:
        self._commits = commits
        self._pr = pr

    async def fetch_pull_request(self, number: int) -> PullRequest:
        if self._pr is None or self._pr.number != number:
            raise KeyError(number)
        return self._pr

    async def fetch_commits(
        self,
        *,
        since: str | None = None,
        branch: str | None = None,
        limit: int = 100,
    ) -> list[GitCommit]:
        return list(self._commits)[:limit]


class FakeRqm:
    def __init__(self, cases: list[RqmTestCase], executions: list[RqmExecution]) -> None:
        self._cases = cases
        self._executions = executions

    async def fetch_test_cases(self) -> list[RqmTestCase]:
        return list(self._cases)

    async def fetch_test_cases_for_requirement(self, requirement_tag: str) -> list[RqmTestCase]:
        tag = requirement_tag.upper()
        return [c for c in self._cases if tag in c.requirement_tags]

    async def fetch_executions(
        self,
        *,
        test_case_id: str | None = None,
        build_id: str | None = None,
    ) -> list[RqmExecution]:
        result = self._executions
        if test_case_id:
            result = [e for e in result if e.test_case_id == test_case_id]
        if build_id:
            result = [e for e in result if e.build_id == build_id]
        return list(result)


class FailingDoors(FakeDoors):
    async def fetch_requirements(self) -> list[Requirement]:
        raise RuntimeError("DOORS unavailable")
