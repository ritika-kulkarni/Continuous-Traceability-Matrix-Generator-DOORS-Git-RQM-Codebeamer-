from datetime import UTC, datetime

import pytest
from tests.fakes import FakeDoors, FakeGit, FakeRqm

from traceability.domain.models import (
    GitCommit,
    PullRequest,
    Requirement,
    RqmExecution,
    RqmTestCase,
    VerificationLevel,
)
from traceability.services.pr_validator import PRValidatorService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pr_compliant_when_tag_and_unit_test_exist(
    sample_requirements: list[Requirement],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
    sample_pr: PullRequest,
) -> None:
    service = PRValidatorService(
        git=FakeGit([], sample_pr),
        doors=FakeDoors(sample_requirements),
        rqm=FakeRqm(sample_test_cases, sample_executions),
    )
    result = await service.validate(42)
    assert result.compliant is True
    assert result.tags_found == ("REQ_ADAS_USS_042",)
    assert result.issues == ()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pr_fails_without_requirement_tag(
    sample_requirements: list[Requirement],
    sample_test_cases: list[RqmTestCase],
) -> None:
    pr = PullRequest(
        number=7,
        title="refactor internals",
        body="no tags here",
        author="dev",
        source_branch="refactor",
        target_branch="main",
        commits=(
            GitCommit(
                sha="deadbeef",
                message="refactor only",
                author="dev",
                committed_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ),
        head_sha="deadbeef",
    )
    service = PRValidatorService(
        git=FakeGit([], pr),
        doors=FakeDoors(sample_requirements),
        rqm=FakeRqm(sample_test_cases, []),
    )
    result = await service.validate(7)
    assert result.compliant is False
    assert result.issues[0].code == "MISSING_REQ_TAG"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pr_fails_when_rqm_case_missing(
    sample_requirements: list[Requirement],
    sample_pr: PullRequest,
) -> None:
    service = PRValidatorService(
        git=FakeGit([], sample_pr),
        doors=FakeDoors(sample_requirements),
        rqm=FakeRqm([], []),
    )
    result = await service.validate(42)
    assert result.compliant is False
    assert any(i.code == "MISSING_TEST_CASE" for i in result.issues)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pr_fails_when_only_system_level_test(
    sample_requirements: list[Requirement],
    sample_pr: PullRequest,
) -> None:
    cases = [
        RqmTestCase(
            id="TC-SYS",
            name="system only",
            level=VerificationLevel.SYSTEM,
            requirement_tags=("REQ_ADAS_USS_042",),
        )
    ]
    service = PRValidatorService(
        git=FakeGit([], sample_pr),
        doors=FakeDoors(sample_requirements),
        rqm=FakeRqm(cases, []),
    )
    result = await service.validate(42)
    assert result.compliant is False
    assert any(i.code == "MISSING_UNIT_OR_INTEGRATION_TEST" for i in result.issues)
