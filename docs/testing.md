# Testing

## Layout

```text
tests/
  conftest.py              # Shared fixtures (sample requirements, commits, …)
  fakes.py                 # In-memory port implementations
  unit/                    # Fast, no network
  integration/             # HTTP mocked with respx + FastAPI TestClient
```

See [tests/README.md](../tests/README.md).

## Commands

```bash
# Full suite
pytest

# By marker
pytest -m unit
pytest -m integration

# Coverage
pytest --cov=traceability --cov-report=term-missing
pytest --cov=traceability --cov-report=html
open htmlcov/index.html

# Lint
ruff check src tests
```

## Markers

Configured in `pyproject.toml`:

| Marker | Intent |
|---|---|
| `unit` | Pure logic, fakes only |
| `integration` | Adapter HTTP + API workflow |

## What is covered

| Area | Tests |
|---|---|
| Tag parser | `tests/unit/test_requirement_tag.py` |
| Matrix gaps | `tests/unit/test_matrix_generator.py` |
| PR gate rules | `tests/unit/test_pr_validator.py` |
| Sync links + fail-soft | `tests/unit/test_sync_service.py` |
| HTML export | `tests/unit/test_html_exporter.py` |
| Adapters + retries | `tests/integration/test_adapters_http.py` |
| API E2E with fakes | `tests/integration/test_api_and_workflow.py` |

## Writing new tests

1. Prefer fakes from `tests/fakes.py` over real network  
2. For HTTP adapters, use `@respx.mock`  
3. Mark tests `@pytest.mark.unit` or `@pytest.mark.integration`  
4. Avoid class names starting with `Test` for domain models (pytest collects them) — use `RqmTestCase`, etc.  

### Example unit test skeleton

```python
import pytest
from tests.fakes import FakeDoors, FakeGit, FakeRqm
from traceability.services.pr_validator import PRValidatorService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_example(sample_pr, sample_requirements, sample_test_cases):
    service = PRValidatorService(
        git=FakeGit([], sample_pr),
        doors=FakeDoors(sample_requirements),
        rqm=FakeRqm(sample_test_cases, []),
    )
    result = await service.validate(42)
    assert result.compliant
```

## PDF tests

PDF generation depends on native WeasyPrint libraries. The suite does not require PDF by default. To exercise PDF locally:

```bash
pip install -e ".[pdf]"
# then call PdfExporter in a manual script or optional test
```

## Continuous integration

`ci.yml` runs `ruff` + `pytest --cov` on every push/PR.
