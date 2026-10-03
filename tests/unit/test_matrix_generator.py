import pytest

from traceability.domain.models import (
    CodeItem,
    GitCommit,
    Requirement,
    RqmExecution,
    RqmTestCase,
)
from traceability.services.matrix_generator import MatrixGeneratorService
from traceability.services.sync_service import TraceabilityStore


@pytest.mark.unit
def test_matrix_marks_complete_and_gaps(
    sample_requirements: list[Requirement],
    sample_code_items: list[CodeItem],
    sample_commits: list[GitCommit],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
) -> None:
    store = TraceabilityStore()
    for r in sample_requirements:
        store.requirements[r.tag] = r
    for i in sample_code_items:
        store.code_items[i.id] = i
    for c in sample_commits:
        store.commits[c.sha] = c
    for t in sample_test_cases:
        store.test_cases[t.id] = t
    store.executions = list(sample_executions)

    matrix = MatrixGeneratorService(store).generate(build_id="nightly-42")
    by_tag = {row.requirement_tag: row for row in matrix.rows}

    uss = by_tag["REQ_ADAS_USS_042"]
    assert uss.coverage_complete is True
    assert uss.gaps == ()
    assert uss.codebeamer_ids == ("CB-501",)
    assert uss.test_case_ids == ("TC-900",)

    cam = by_tag["REQ_ADAS_CAM_010"]
    assert cam.coverage_complete is False
    assert "missing_codebeamer_link" in cam.gaps
    assert "missing_git_implementation" in cam.gaps
    assert "missing_test_case" in cam.gaps

    assert "REQ_ADAS_CAM_010" in matrix.orphan_requirements
    assert "TC-901" in matrix.orphan_tests
    assert matrix.summary["rows_complete"] == 1
    assert matrix.summary["requirements_total"] == 2
