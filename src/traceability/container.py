"""Composition root — wires adapters and services from settings."""

from __future__ import annotations

from dataclasses import dataclass

from traceability.adapters import CodebeamerAdapter, DoorsAdapter, GitAdapter, RqmAdapter
from traceability.config import Settings, load_settings
from traceability.domain.requirement_tag import RequirementTagParser
from traceability.exporters import HtmlExporter, PdfExporter
from traceability.services import (
    MatrixGeneratorService,
    PRValidatorService,
    SyncService,
    TraceabilityStore,
)


@dataclass
class AppContainer:
    settings: Settings
    store: TraceabilityStore
    tag_parser: RequirementTagParser
    doors: DoorsAdapter
    codebeamer: CodebeamerAdapter
    git: GitAdapter
    rqm: RqmAdapter
    sync_service: SyncService
    pr_validator: PRValidatorService
    matrix_generator: MatrixGeneratorService
    html_exporter: HtmlExporter
    pdf_exporter: PdfExporter

    async def aclose(self) -> None:
        for adapter in (self.doors, self.codebeamer, self.git, self.rqm):
            close = getattr(adapter, "aclose", None)
            if close is not None:
                await close()


def build_container(
    settings: Settings | None = None,
    config_path: str | None = None,
) -> AppContainer:
    cfg = settings or load_settings(config_path)
    tag_parser = RequirementTagParser(cfg.app.req_tag_pattern)
    store = TraceabilityStore()

    doors = DoorsAdapter(cfg.doors, tag_parser=tag_parser)
    codebeamer = CodebeamerAdapter(cfg.codebeamer, tag_parser=tag_parser)
    git = GitAdapter(cfg.git, tag_parser=tag_parser)
    rqm = RqmAdapter(cfg.rqm, tag_parser=tag_parser)

    sync_service = SyncService(
        doors=doors,
        codebeamer=codebeamer,
        git=git,
        rqm=rqm,
        store=store,
        fail_fast=cfg.sync.fail_fast,
    )
    pr_validator = PRValidatorService(
        git=git,
        doors=doors,
        rqm=rqm,
        tag_parser=tag_parser,
    )
    matrix_generator = MatrixGeneratorService(
        store,
        title=cfg.matrix.title,
        include_orphan_requirements=cfg.matrix.include_orphan_requirements,
        include_orphan_tests=cfg.matrix.include_orphan_tests,
    )
    html_exporter = HtmlExporter(template_name=cfg.matrix.html_template)
    pdf_exporter = PdfExporter(html_exporter)

    return AppContainer(
        settings=cfg,
        store=store,
        tag_parser=tag_parser,
        doors=doors,
        codebeamer=codebeamer,
        git=git,
        rqm=rqm,
        sync_service=sync_service,
        pr_validator=pr_validator,
        matrix_generator=matrix_generator,
        html_exporter=html_exporter,
        pdf_exporter=pdf_exporter,
    )
