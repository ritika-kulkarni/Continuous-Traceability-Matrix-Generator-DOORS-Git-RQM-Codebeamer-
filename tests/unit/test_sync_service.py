import pytest
from tests.fakes import (
    FailingDoors,
    FakeCodebeamer,
    FakeDoors,
    FakeGit,
    FakeRqm,
)

from traceability.domain.models import (
    CodeItem,
    GitCommit,
    LinkType,
    Requirement,
    RqmExecution,
    RqmTestCase,
)
from traceability.services.sync_service import SyncService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_builds_bidirectional_links(
    sample_requirements: list[Requirement],
    sample_code_items: list[CodeItem],
    sample_commits: list[GitCommit],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
) -> None:
    service = SyncService(
        doors=FakeDoors(sample_requirements),
        codebeamer=FakeCodebeamer(sample_code_items),
        git=FakeGit(sample_commits),
        rqm=FakeRqm(sample_test_cases, sample_executions),
    )
    result = await service.sync_all(build_id="nightly-42")

    assert result.requirements_synced == 2
    assert result.code_items_synced == 1
    assert result.commits_synced == 1
    assert result.tests_synced == 2
    assert result.errors == ()

    link_types = {link.link_type for link in service.store.links}
    assert LinkType.SATISFIES in link_types
    assert LinkType.IMPLEMENTS in link_types
    assert LinkType.VERIFIES in link_types


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_continues_when_source_fails(
    sample_code_items: list[CodeItem],
    sample_commits: list[GitCommit],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
) -> None:
    service = SyncService(
        doors=FailingDoors([]),
        codebeamer=FakeCodebeamer(sample_code_items),
        git=FakeGit(sample_commits),
        rqm=FakeRqm(sample_test_cases, sample_executions),
        fail_fast=False,
    )
    result = await service.sync_all()
    assert result.requirements_synced == 0
    assert result.code_items_synced == 1
    assert any("DOORS unavailable" in e for e in result.errors)
