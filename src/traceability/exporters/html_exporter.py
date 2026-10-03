"""HTML export for the ASPICE traceability matrix."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from traceability.domain.models import TraceabilityMatrix
from traceability.exceptions import ExportError


class HtmlExporter:
    def __init__(
        self,
        template_dir: str | Path | None = None,
        template_name: str = "matrix.html.j2",
    ) -> None:
        default_dir = Path(__file__).resolve().parent / "templates"
        self._template_dir = Path(template_dir) if template_dir else default_dir
        self._template_name = template_name
        template_path = self._template_dir / self._template_name
        if not template_path.is_file():
            raise ExportError(f"HTML template not found: {template_path}")
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )

    def render(self, matrix: TraceabilityMatrix) -> str:
        template = self._env.get_template(self._template_name)
        return template.render(matrix=matrix)

    def write(self, matrix: TraceabilityMatrix, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(matrix), encoding="utf-8")
        return path
