"""Ports (interfaces) for external systems — Dependency Inversion."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from traceability.domain.models import (
    CodeItem,
    GitCommit,
    PullRequest,
    Requirement,
    RqmExecution,
    RqmTestCase,
)


@runtime_checkable
class RequirementsPort(Protocol):
    async def fetch_requirements(self) -> list[Requirement]: ...

    async def get_requirement_by_tag(self, tag: str) -> Requirement | None: ...


@runtime_checkable
class CodebeamerPort(Protocol):
    async def fetch_items(self) -> list[CodeItem]: ...

    async def fetch_items_for_requirement(self, requirement_tag: str) -> list[CodeItem]: ...


@runtime_checkable
class GitPort(Protocol):
    async def fetch_pull_request(self, number: int) -> PullRequest: ...

    async def fetch_commits(
        self,
        *,
        since: str | None = None,
        branch: str | None = None,
        limit: int = 100,
    ) -> list[GitCommit]: ...


@runtime_checkable
class RqmPort(Protocol):
    async def fetch_test_cases(self) -> list[RqmTestCase]: ...

    async def fetch_test_cases_for_requirement(self, requirement_tag: str) -> list[RqmTestCase]: ...

    async def fetch_executions(
        self,
        *,
        test_case_id: str | None = None,
        build_id: str | None = None,
    ) -> list[RqmExecution]: ...
