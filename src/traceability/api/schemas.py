"""API request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from traceability.domain.models import PRValidationResult, SyncResult, TraceabilityMatrix


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str


class SyncRequest(BaseModel):
    git_since: str | None = None
    git_branch: str | None = None
    build_id: str | None = None


class SyncResponse(BaseModel):
    result: SyncResult


class PRValidateRequest(BaseModel):
    pr_number: int = Field(ge=1)


class PRValidateResponse(BaseModel):
    result: PRValidationResult


class MatrixGenerateRequest(BaseModel):
    build_id: str | None = None
    sync_first: bool = True
    git_since: str | None = None
    git_branch: str | None = None
    export_html: bool = True
    export_pdf: bool = False


class MatrixGenerateResponse(BaseModel):
    matrix: TraceabilityMatrix
    html_path: str | None = None
    pdf_path: str | None = None
    generated_at: datetime
