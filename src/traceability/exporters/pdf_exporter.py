"""PDF export via WeasyPrint (HTML → PDF)."""

from __future__ import annotations

from pathlib import Path

from traceability.domain.models import TraceabilityMatrix
from traceability.exceptions import ExportError
from traceability.exporters.html_exporter import HtmlExporter


class PdfExporter:
    def __init__(self, html_exporter: HtmlExporter | None = None) -> None:
        self._html = html_exporter or HtmlExporter()

    def write(self, matrix: TraceabilityMatrix, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        html = self._html.render(matrix)
        try:
            from weasyprint import HTML
        except Exception as exc:  # pragma: no cover - optional native deps
            raise ExportError(
                "WeasyPrint is unavailable. Install system libraries or export HTML only."
            ) from exc
        try:
            HTML(string=html, base_url=str(Path.cwd())).write_pdf(str(path))
        except Exception as exc:
            raise ExportError(f"PDF generation failed: {exc}") from exc
        return path
