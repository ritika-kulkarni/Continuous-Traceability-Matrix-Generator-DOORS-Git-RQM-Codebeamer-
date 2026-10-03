"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from traceability.domain.models import (
    ArtifactSource,
    CodeItem,
    ExecutionStatus,
    GitCommit,
    PullRequest,
    Requirement,
    RqmExecution,
    RqmTestCase,
    VerificationLevel,
)
from traceability.domain.requirement_tag import RequirementTagParser


@pytest.fixture
def tag_parser() -> RequirementTagParser:
    return RequirementTagParser()


@pytest.fixture
def sample_requirements() -> list[Requirement]:
    return [
        Requirement(
            id="D-100",
            tag="REQ_ADAS_USS_042",
            title="Ultrasonic obstacle detection within 2m",
            source=ArtifactSource.DOORS,
            module="/ADAS/USS",
        ),
        Requirement(
            id="D-101",
            tag="REQ_ADAS_CAM_010",
            title="Camera lane detection",
            source=ArtifactSource.DOORS,
            module="/ADAS/CAM",
        ),
    ]


@pytest.fixture
def sample_code_items() -> list[CodeItem]:
    return [
        CodeItem(
            id="CB-501",
            title="USS ranging SW design",
            item_type="Design",
            requirement_tags=("REQ_ADAS_USS_042",),
        )
    ]


@pytest.fixture
def sample_commits() -> list[GitCommit]:
    return [
        GitCommit(
            sha="abc123def4567890",
            message="feat: implement USS ranging\n\nRequires: REQ_ADAS_USS_042",
            author="engineer",
            committed_at=datetime(2026, 3, 1, tzinfo=UTC),
            requirement_tags=("REQ_ADAS_USS_042",),
        )
    ]


@pytest.fixture
def sample_test_cases() -> list[RqmTestCase]:
    return [
        RqmTestCase(
            id="TC-900",
            name="USS unit: range accuracy",
            level=VerificationLevel.UNIT,
            requirement_tags=("REQ_ADAS_USS_042",),
        ),
        RqmTestCase(
            id="TC-901",
            name="Orphan test without req",
            level=VerificationLevel.SYSTEM,
            requirement_tags=(),
        ),
    ]


@pytest.fixture
def sample_executions() -> list[RqmExecution]:
    return [
        RqmExecution(
            id="EX-1",
            test_case_id="TC-900",
            status=ExecutionStatus.PASSED,
            executed_at=datetime(2026, 3, 2, tzinfo=UTC),
            build_id="nightly-42",
        )
    ]


@pytest.fixture
def sample_pr(sample_commits: list[GitCommit]) -> PullRequest:
    return PullRequest(
        number=42,
        title="feat: USS ranging REQ_ADAS_USS_042",
        body="Implements ultrasonic ranging.",
        author="engineer",
        source_branch="feature/uss",
        target_branch="main",
        commits=tuple(sample_commits),
        head_sha=sample_commits[0].sha,
        url="https://github.com/org/ecu-firmware/pull/42",
    )
