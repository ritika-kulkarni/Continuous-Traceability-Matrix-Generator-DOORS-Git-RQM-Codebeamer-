"""Pull-request gate: require REQ_* tags and matching RQM test coverage."""

from __future__ import annotations

from traceability.domain.models import (
    PRValidationIssue,
    PRValidationResult,
    PullRequest,
    VerificationLevel,
)
from traceability.domain.requirement_tag import RequirementTagParser
from traceability.logging_setup import get_logger
from traceability.ports import GitPort, RequirementsPort, RqmPort

logger = get_logger(__name__)


class PRValidatorService:
    """Validates that a PR is ASPICE-traceable before merge."""

    def __init__(
        self,
        *,
        git: GitPort,
        doors: RequirementsPort,
        rqm: RqmPort,
        tag_parser: RequirementTagParser | None = None,
        require_unit_or_integration: bool = True,
    ) -> None:
        self._git = git
        self._doors = doors
        self._rqm = rqm
        self._tag_parser = tag_parser or RequirementTagParser()
        self._require_unit_or_integration = require_unit_or_integration

    async def validate(self, pr_number: int) -> PRValidationResult:
        pr = await self._git.fetch_pull_request(pr_number)
        return await self.validate_pull_request(pr)

    async def validate_pull_request(self, pr: PullRequest) -> PRValidationResult:
        tags = self._collect_tags(pr)
        issues: list[PRValidationIssue] = []

        if not tags:
            issues.append(
                PRValidationIssue(
                    severity="error",
                    code="MISSING_REQ_TAG",
                    message=(
                        "No compliant requirement tags found in PR title/body/commits. "
                        "Expected form like REQ_ADAS_USS_042."
                    ),
                )
            )
            return PRValidationResult(
                pr_number=pr.number,
                compliant=False,
                tags_found=(),
                issues=tuple(issues),
            )

        for tag in tags:
            if not self._tag_parser.is_valid(tag):
                issues.append(
                    PRValidationIssue(
                        severity="error",
                        code="INVALID_REQ_TAG",
                        message=f"Tag '{tag}' does not match the required pattern.",
                        requirement_tag=tag,
                    )
                )
                continue

            requirement = await self._doors.get_requirement_by_tag(tag)
            if requirement is None:
                issues.append(
                    PRValidationIssue(
                        severity="error",
                        code="UNKNOWN_REQUIREMENT",
                        message=f"Requirement '{tag}' was not found in DOORS/Codebeamer.",
                        requirement_tag=tag,
                    )
                )
                continue

            cases = await self._rqm.fetch_test_cases_for_requirement(tag)
            if not cases:
                issues.append(
                    PRValidationIssue(
                        severity="error",
                        code="MISSING_TEST_CASE",
                        message=f"No RQM test case linked to '{tag}'.",
                        requirement_tag=tag,
                    )
                )
                continue

            if self._require_unit_or_integration:
                allowed = {VerificationLevel.UNIT, VerificationLevel.INTEGRATION}
                eligible = {c.level for c in cases if c.level in allowed}
                if not eligible:
                    issues.append(
                        PRValidationIssue(
                            severity="error",
                            code="MISSING_UNIT_OR_INTEGRATION_TEST",
                            message=(
                                f"Requirement '{tag}' has RQM cases but none at unit/integration "
                                "level."
                            ),
                            requirement_tag=tag,
                        )
                    )

        errors = [i for i in issues if i.severity == "error"]
        result = PRValidationResult(
            pr_number=pr.number,
            compliant=len(errors) == 0,
            tags_found=tags,
            issues=tuple(issues),
        )
        logger.info(
            "pr_validated",
            pr_number=pr.number,
            compliant=result.compliant,
            tags=list(tags),
            issue_count=len(issues),
        )
        return result

    def _collect_tags(self, pr: PullRequest) -> tuple[str, ...]:
        blobs = [pr.title, pr.body]
        for commit in pr.commits:
            blobs.append(commit.message)
        found: set[str] = set()
        for blob in blobs:
            found.update(self._tag_parser.extract(blob))
        # Prefer commit-header extraction for richer accuracy
        for commit in pr.commits:
            found.update(self._tag_parser.extract_from_commit_message(commit.message))
        return tuple(sorted(found))
