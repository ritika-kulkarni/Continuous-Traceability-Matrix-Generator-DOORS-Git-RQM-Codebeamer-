from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.fakes import FakeCodebeamer, FakeDoors, FakeGit, FakeRqm

from traceability import __version__
from traceability.api.app import create_app
from traceability.config import Settings
from traceability.container import AppContainer
from traceability.domain.models import (
    CodeItem,
    GitCommit,
    PullRequest,
    Requirement,
    RqmExecution,
    RqmTestCase,
)
from traceability.domain.requirement_tag import RequirementTagParser
from traceability.exporters import HtmlExporter, PdfExporter
from traceability.services import (
    MatrixGeneratorService,
    PRValidatorService,
    SyncService,
    TraceabilityStore,
)


def _container_with_fakes(
    *,
    requirements: list[Requirement],
    code_items: list[CodeItem],
    commits: list[GitCommit],
    test_cases: list[RqmTestCase],
    executions: list[RqmExecution],
    pr: PullRequest,
    output_dir: Path,
) -> AppContainer:
    settings = Settings()
    settings.matrix.output_dir = str(output_dir)
    store = TraceabilityStore()
    tag_parser = RequirementTagParser()
    doors = FakeDoors(requirements)
    codebeamer = FakeCodebeamer(code_items)
    git = FakeGit(commits, pr)
    rqm = FakeRqm(test_cases, executions)
    sync_service = SyncService(
        doors=doors, codebeamer=codebeamer, git=git, rqm=rqm, store=store
    )
    pr_validator = PRValidatorService(git=git, doors=doors, rqm=rqm, tag_parser=tag_parser)
    matrix_generator = MatrixGeneratorService(store, title=settings.matrix.title)
    html_exporter = HtmlExporter()
    pdf_exporter = PdfExporter(html_exporter)

    # Adapters are duck-typed; Fake* satisfy ports used by services/API.
    return AppContainer(
        settings=settings,
        store=store,
        tag_parser=tag_parser,
        doors=doors,  # type: ignore[arg-type]
        codebeamer=codebeamer,  # type: ignore[arg-type]
        git=git,  # type: ignore[arg-type]
        rqm=rqm,  # type: ignore[arg-type]
        sync_service=sync_service,
        pr_validator=pr_validator,
        matrix_generator=matrix_generator,
        html_exporter=html_exporter,
        pdf_exporter=pdf_exporter,
    )


@pytest.mark.integration
def test_health_and_end_to_end_matrix_api(
    tmp_path: Path,
    sample_requirements: list[Requirement],
    sample_code_items: list[CodeItem],
    sample_commits: list[GitCommit],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
    sample_pr: PullRequest,
) -> None:
    container = _container_with_fakes(
        requirements=sample_requirements,
        code_items=sample_code_items,
        commits=sample_commits,
        test_cases=sample_test_cases,
        executions=sample_executions,
        pr=sample_pr,
        output_dir=tmp_path,
    )
    app = create_app(container)
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["version"] == __version__

        pr_resp = client.post("/api/v1/pr/validate", json={"pr_number": 42})
        assert pr_resp.status_code == 200
        assert pr_resp.json()["result"]["compliant"] is True

        matrix_resp = client.post(
            "/api/v1/matrix/generate",
            json={
                "build_id": "nightly-42",
                "sync_first": True,
                "export_html": True,
                "export_pdf": False,
            },
        )
        assert matrix_resp.status_code == 200
        body = matrix_resp.json()
        assert body["matrix"]["summary"]["requirements_total"] == 2
        assert body["html_path"] is not None
        assert Path(body["html_path"]).is_file()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nightly_workflow_service_path(
    tmp_path: Path,
    sample_requirements: list[Requirement],
    sample_code_items: list[CodeItem],
    sample_commits: list[GitCommit],
    sample_test_cases: list[RqmTestCase],
    sample_executions: list[RqmExecution],
) -> None:
    store = TraceabilityStore()
    sync = SyncService(
        doors=FakeDoors(sample_requirements),
        codebeamer=FakeCodebeamer(sample_code_items),
        git=FakeGit(sample_commits),
        rqm=FakeRqm(sample_test_cases, sample_executions),
        store=store,
    )
    await sync.sync_all(build_id="nightly-42")
    matrix = MatrixGeneratorService(store).generate(build_id="nightly-42")
    html_path = HtmlExporter().write(matrix, tmp_path / "nightly.html")
    assert "REQ_ADAS_USS_042" in html_path.read_text(encoding="utf-8")
    assert matrix.summary["rows_complete"] == 1
