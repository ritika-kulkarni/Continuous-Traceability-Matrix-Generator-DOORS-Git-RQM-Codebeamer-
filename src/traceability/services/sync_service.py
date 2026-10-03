"""Synchronization orchestration across DOORS, Codebeamer, Git, and RQM."""

from __future__ import annotations

from dataclasses import dataclass, field

from traceability.domain.models import (
    CodeItem,
    GitCommit,
    LinkType,
    Requirement,
    RqmExecution,
    RqmTestCase,
    SyncResult,
    TraceLink,
    utc_now,
)
from traceability.logging_setup import get_logger
from traceability.ports import CodebeamerPort, GitPort, RequirementsPort, RqmPort

logger = get_logger(__name__)


@dataclass
class TraceabilityStore:
    """In-memory aggregate used by matrix generation and API queries.

    Replace with a persistent repository for multi-instance deployments.
    """

    requirements: dict[str, Requirement] = field(default_factory=dict)
    code_items: dict[str, CodeItem] = field(default_factory=dict)
    commits: dict[str, GitCommit] = field(default_factory=dict)
    test_cases: dict[str, RqmTestCase] = field(default_factory=dict)
    executions: list[RqmExecution] = field(default_factory=list)
    links: list[TraceLink] = field(default_factory=list)

    def clear(self) -> None:
        self.requirements.clear()
        self.code_items.clear()
        self.commits.clear()
        self.test_cases.clear()
        self.executions.clear()
        self.links.clear()


class SyncService:
    """Pulls artifacts from all systems and builds bidirectional links."""

    def __init__(
        self,
        *,
        doors: RequirementsPort,
        codebeamer: CodebeamerPort,
        git: GitPort,
        rqm: RqmPort,
        store: TraceabilityStore | None = None,
        fail_fast: bool = False,
    ) -> None:
        self._doors = doors
        self._codebeamer = codebeamer
        self._git = git
        self._rqm = rqm
        self.store = store or TraceabilityStore()
        self._fail_fast = fail_fast

    async def sync_all(
        self,
        *,
        git_since: str | None = None,
        git_branch: str | None = None,
        build_id: str | None = None,
    ) -> SyncResult:
        started = utc_now()
        errors: list[str] = []
        self.store.clear()

        requirements = await self._safe_fetch("doors", self._doors.fetch_requirements(), errors)
        code_items = await self._safe_fetch("codebeamer", self._codebeamer.fetch_items(), errors)
        commits = await self._safe_fetch(
            "git",
            self._git.fetch_commits(since=git_since, branch=git_branch),
            errors,
        )
        test_cases = await self._safe_fetch("rqm", self._rqm.fetch_test_cases(), errors)
        executions = await self._safe_fetch(
            "rqm",
            self._rqm.fetch_executions(build_id=build_id),
            errors,
        )

        for req in requirements:
            self.store.requirements[req.tag] = req
        for item in code_items:
            self.store.code_items[item.id] = item
        for commit in commits:
            self.store.commits[commit.sha] = commit
        for case in test_cases:
            self.store.test_cases[case.id] = case
        self.store.executions = list(executions)

        links = self._build_links()
        self.store.links = links

        result = SyncResult(
            requirements_synced=len(requirements),
            code_items_synced=len(code_items),
            commits_synced=len(commits),
            tests_synced=len(test_cases),
            links_created=len(links),
            errors=tuple(errors),
            started_at=started,
            finished_at=utc_now(),
        )
        logger.info(
            "sync_completed",
            requirements=result.requirements_synced,
            code_items=result.code_items_synced,
            commits=result.commits_synced,
            tests=result.tests_synced,
            links=result.links_created,
            errors=len(errors),
        )
        return result

    async def _safe_fetch(self, system: str, awaitable, errors: list[str]):  # type: ignore[no-untyped-def]
        try:
            return await awaitable
        except Exception as exc:
            message = f"{system}: {exc}"
            logger.error("sync_source_failed", system=system, error=str(exc))
            if self._fail_fast:
                raise
            errors.append(message)
            return []

    def _build_links(self) -> list[TraceLink]:
        links: list[TraceLink] = []

        for item in self.store.code_items.values():
            for tag in item.requirement_tags:
                if tag in self.store.requirements:
                    links.append(
                        TraceLink(
                            source_id=item.id,
                            source_kind="codebeamer",
                            target_id=tag,
                            target_kind="requirement",
                            link_type=LinkType.SATISFIES,
                            evidence=item.title,
                        )
                    )

        for commit in self.store.commits.values():
            for tag in commit.requirement_tags:
                if tag in self.store.requirements:
                    links.append(
                        TraceLink(
                            source_id=commit.sha,
                            source_kind="git_commit",
                            target_id=tag,
                            target_kind="requirement",
                            link_type=LinkType.IMPLEMENTS,
                            evidence=commit.message.splitlines()[0][:200],
                        )
                    )

        for case in self.store.test_cases.values():
            for tag in case.requirement_tags:
                if tag in self.store.requirements:
                    links.append(
                        TraceLink(
                            source_id=case.id,
                            source_kind="test_case",
                            target_id=tag,
                            target_kind="requirement",
                            link_type=LinkType.VERIFIES,
                            evidence=case.name,
                        )
                    )

        return links
