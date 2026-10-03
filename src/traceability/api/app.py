"""FastAPI application for the synchronization service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from traceability import __version__
from traceability.api.schemas import (
    HealthResponse,
    MatrixGenerateRequest,
    MatrixGenerateResponse,
    PRValidateRequest,
    PRValidateResponse,
    SyncRequest,
    SyncResponse,
)
from traceability.container import AppContainer, build_container
from traceability.exceptions import AdapterError, NotFoundError, TraceabilityError
from traceability.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)


def create_app(container: AppContainer | None = None) -> FastAPI:
    state: dict[str, AppContainer] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cfg_container = container or build_container()
        configure_logging(cfg_container.settings.app.log_level)
        state["container"] = cfg_container
        app.state.container = cfg_container
        logger.info("api_started", version=__version__)
        try:
            yield
        finally:
            await cfg_container.aclose()

    app = FastAPI(
        title="ASPICE Traceability Sync Service",
        version=__version__,
        description=(
            "Python/REST synchronization service linking IBM DOORS / Codebeamer IDs, "
            "Git commit headers, and RQM test execution logs."
        ),
        lifespan=lifespan,
    )

    def get_container() -> AppContainer:
        return state["container"]

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        c = get_container()
        return HealthResponse(
            status="ok",
            service=c.settings.app.name,
            version=__version__,
        )

    @app.post("/api/v1/sync", response_model=SyncResponse)
    async def sync(request: SyncRequest) -> SyncResponse:
        c = get_container()
        try:
            result = await c.sync_service.sync_all(
                git_since=request.git_since,
                git_branch=request.git_branch,
                build_id=request.build_id,
            )
        except AdapterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return SyncResponse(result=result)

    @app.post("/api/v1/pr/validate", response_model=PRValidateResponse)
    async def validate_pr(request: PRValidateRequest) -> PRValidateResponse:
        c = get_container()
        try:
            result = await c.pr_validator.validate(request.pr_number)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AdapterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return PRValidateResponse(result=result)

    @app.post("/api/v1/matrix/generate", response_model=MatrixGenerateResponse)
    async def generate_matrix(request: MatrixGenerateRequest) -> MatrixGenerateResponse:
        c = get_container()
        try:
            if request.sync_first:
                await c.sync_service.sync_all(
                    git_since=request.git_since,
                    git_branch=request.git_branch,
                    build_id=request.build_id,
                )
            matrix = c.matrix_generator.generate(build_id=request.build_id)
            output_dir = Path(c.settings.matrix.output_dir)
            stamp = matrix.generated_at.strftime("%Y%m%dT%H%M%SZ")
            html_path = None
            pdf_path = None
            if request.export_html:
                html_path = str(
                    c.html_exporter.write(matrix, output_dir / f"traceability_matrix_{stamp}.html")
                )
            if request.export_pdf:
                pdf_path = str(
                    c.pdf_exporter.write(matrix, output_dir / f"traceability_matrix_{stamp}.pdf")
                )
        except TraceabilityError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return MatrixGenerateResponse(
            matrix=matrix,
            html_path=html_path,
            pdf_path=pdf_path,
            generated_at=matrix.generated_at,
        )

    return app


app = create_app()
