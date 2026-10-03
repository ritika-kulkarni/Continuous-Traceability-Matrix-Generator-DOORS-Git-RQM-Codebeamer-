"""Domain entities for ASPICE bidirectional traceability.

These models are framework-agnostic and form the canonical representation
shared across DOORS, Codebeamer, Git, and RQM adapters.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArtifactSource(StrEnum):
    DOORS = "doors"
    CODEBEAMER = "codebeamer"
    GIT = "git"
    RQM = "rqm"


class LinkType(StrEnum):
    SATISFIES = "satisfies"  # design/code → requirement
    VERIFIES = "verifies"  # test → requirement
    IMPLEMENTS = "implements"  # commit → requirement
    DERIVES = "derives"  # child requirement → parent


class VerificationLevel(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"


class ExecutionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"
    INCONCLUSIVE = "inconclusive"


class Requirement(BaseModel):
    """Customer or system requirement from DOORS / Codebeamer."""

    model_config = ConfigDict(frozen=True)

    id: str
    tag: str
    title: str
    description: str = ""
    source: ArtifactSource
    module: str | None = None
    status: str = "Approved"
    parent_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    last_modified: datetime | None = None

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, value: str) -> str:
        return value.strip().upper()


class CodeItem(BaseModel):
    """Codebeamer work item or design artifact linked to a requirement."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    item_type: str
    requirement_ids: tuple[str, ...] = ()
    requirement_tags: tuple[str, ...] = ()
    url: str | None = None
    status: str = "In Progress"


class GitCommit(BaseModel):
    """Git commit carrying requirement tags in message headers."""

    model_config = ConfigDict(frozen=True)

    sha: str
    message: str
    author: str
    committed_at: datetime
    branch: str | None = None
    pr_number: int | None = None
    requirement_tags: tuple[str, ...] = ()
    files_changed: tuple[str, ...] = ()


class PullRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    title: str
    body: str = ""
    author: str
    source_branch: str
    target_branch: str
    commits: tuple[GitCommit, ...] = ()
    head_sha: str
    url: str | None = None


class RqmTestCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    level: VerificationLevel
    requirement_tags: tuple[str, ...] = ()
    script_path: str | None = None


class RqmExecution(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    test_case_id: str
    status: ExecutionStatus
    executed_at: datetime
    build_id: str | None = None
    requirement_tags: tuple[str, ...] = ()
    log_url: str | None = None


class TraceLink(BaseModel):
    """Directed link between two artifacts in the traceability graph."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_kind: str
    target_id: str
    target_kind: str
    link_type: LinkType
    evidence: str | None = None


class TraceRow(BaseModel):
    """One row of the ASPICE end-to-end matrix."""

    model_config = ConfigDict(frozen=True)

    requirement_tag: str
    requirement_id: str
    requirement_title: str
    doors_module: str | None = None
    codebeamer_ids: tuple[str, ...] = ()
    commit_shas: tuple[str, ...] = ()
    test_case_ids: tuple[str, ...] = ()
    latest_execution_status: ExecutionStatus | None = None
    coverage_complete: bool = False
    gaps: tuple[str, ...] = ()


class TraceabilityMatrix(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    generated_at: datetime = Field(default_factory=utc_now)
    build_id: str | None = None
    rows: tuple[TraceRow, ...] = ()
    orphan_requirements: tuple[str, ...] = ()
    orphan_tests: tuple[str, ...] = ()
    summary: dict[str, int] = Field(default_factory=dict)


class PRValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    severity: str  # error | warning
    code: str
    message: str
    requirement_tag: str | None = None


class PRValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    pr_number: int
    compliant: bool
    tags_found: tuple[str, ...] = ()
    issues: tuple[PRValidationIssue, ...] = ()
    validated_at: datetime = Field(default_factory=utc_now)


class SyncResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    requirements_synced: int = 0
    code_items_synced: int = 0
    commits_synced: int = 0
    tests_synced: int = 0
    links_created: int = 0
    errors: tuple[str, ...] = ()
    started_at: datetime
    finished_at: datetime = Field(default_factory=utc_now)
