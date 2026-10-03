"""Build the ASPICE end-to-end bidirectional traceability matrix."""

from __future__ import annotations

from collections import defaultdict

from traceability.domain.models import (
    ExecutionStatus,
    TraceabilityMatrix,
    TraceRow,
    utc_now,
)
from traceability.logging_setup import get_logger
from traceability.services.sync_service import TraceabilityStore

logger = get_logger(__name__)


class MatrixGeneratorService:
    def __init__(
        self,
        store: TraceabilityStore,
        *,
        title: str = "ASPICE Bidirectional Traceability Matrix",
        include_orphan_requirements: bool = True,
        include_orphan_tests: bool = True,
    ) -> None:
        self._store = store
        self._title = title
        self._include_orphan_requirements = include_orphan_requirements
        self._include_orphan_tests = include_orphan_tests

    def generate(self, *, build_id: str | None = None) -> TraceabilityMatrix:
        code_by_tag: dict[str, list[str]] = defaultdict(list)
        commits_by_tag: dict[str, list[str]] = defaultdict(list)
        tests_by_tag: dict[str, list[str]] = defaultdict(list)

        for item in self._store.code_items.values():
            for tag in item.requirement_tags:
                code_by_tag[tag].append(item.id)

        for commit in self._store.commits.values():
            for tag in commit.requirement_tags:
                commits_by_tag[tag].append(commit.sha[:12])

        for case in self._store.test_cases.values():
            for tag in case.requirement_tags:
                tests_by_tag[tag].append(case.id)

        latest_status_by_case = self._latest_execution_status()

        rows: list[TraceRow] = []
        covered_tags: set[str] = set()

        for tag, requirement in sorted(self._store.requirements.items()):
            cb_ids = tuple(sorted(set(code_by_tag.get(tag, []))))
            shas = tuple(sorted(set(commits_by_tag.get(tag, []))))
            case_ids = tuple(sorted(set(tests_by_tag.get(tag, []))))

            gaps: list[str] = []
            if not cb_ids:
                gaps.append("missing_codebeamer_link")
            if not shas:
                gaps.append("missing_git_implementation")
            if not case_ids:
                gaps.append("missing_test_case")

            statuses = [
                latest_status_by_case[cid]
                for cid in case_ids
                if cid in latest_status_by_case
            ]
            latest_status = statuses[0] if statuses else None
            if case_ids and latest_status is None:
                gaps.append("missing_test_execution")
            elif latest_status in {ExecutionStatus.FAILED, ExecutionStatus.BLOCKED}:
                gaps.append("failing_or_blocked_execution")

            complete = len(gaps) == 0
            if complete:
                covered_tags.add(tag)

            rows.append(
                TraceRow(
                    requirement_tag=tag,
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    doors_module=requirement.module,
                    codebeamer_ids=cb_ids,
                    commit_shas=shas,
                    test_case_ids=case_ids,
                    latest_execution_status=latest_status,
                    coverage_complete=complete,
                    gaps=tuple(gaps),
                )
            )

        orphan_requirements = tuple(
            sorted(tag for tag in self._store.requirements if tag not in covered_tags)
        )
        referenced_test_ids = {cid for row in rows for cid in row.test_case_ids}
        orphan_tests = tuple(
            sorted(
                case_id
                for case_id, case in self._store.test_cases.items()
                if case_id not in referenced_test_ids or not case.requirement_tags
            )
        )

        summary = {
            "requirements_total": len(self._store.requirements),
            "rows_complete": sum(1 for r in rows if r.coverage_complete),
            "rows_with_gaps": sum(1 for r in rows if not r.coverage_complete),
            "orphan_requirements": (
                len(orphan_requirements) if self._include_orphan_requirements else 0
            ),
            "orphan_tests": len(orphan_tests) if self._include_orphan_tests else 0,
            "links": len(self._store.links),
        }

        matrix = TraceabilityMatrix(
            title=self._title,
            generated_at=utc_now(),
            build_id=build_id,
            rows=tuple(rows),
            orphan_requirements=orphan_requirements if self._include_orphan_requirements else (),
            orphan_tests=orphan_tests if self._include_orphan_tests else (),
            summary=summary,
        )
        logger.info("matrix_generated", **summary)
        return matrix

    def _latest_execution_status(self) -> dict[str, ExecutionStatus]:
        latest: dict[str, tuple[object, ExecutionStatus]] = {}
        for execution in self._store.executions:
            previous = latest.get(execution.test_case_id)
            if previous is None or execution.executed_at > previous[0]:  # type: ignore[operator]
                latest[execution.test_case_id] = (execution.executed_at, execution.status)
        return {case_id: status for case_id, (_, status) in latest.items()}
