from pathlib import Path

import pytest

from traceability.domain.models import TraceabilityMatrix, TraceRow
from traceability.exporters.html_exporter import HtmlExporter


@pytest.mark.unit
def test_html_exporter_writes_artifact(tmp_path: Path) -> None:
    matrix = TraceabilityMatrix(
        title="Test Matrix",
        build_id="b1",
        rows=(
            TraceRow(
                requirement_tag="REQ_ADAS_USS_042",
                requirement_id="D-100",
                requirement_title="USS",
                coverage_complete=True,
            ),
        ),
        summary={"requirements_total": 1, "rows_complete": 1, "rows_with_gaps": 0, "links": 0},
    )
    out = tmp_path / "matrix.html"
    path = HtmlExporter().write(matrix, out)
    content = path.read_text(encoding="utf-8")
    assert "REQ_ADAS_USS_042" in content
    assert "COMPLETE" in content
    assert "Test Matrix" in content
