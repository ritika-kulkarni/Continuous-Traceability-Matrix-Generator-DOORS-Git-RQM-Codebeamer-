# Integration tests

Cross-component tests with **mocked HTTP** (`respx`) or an in-process FastAPI app wired to fakes.

| File | Focus |
|---|---|
| `test_adapters_http.py` | DOORS / Git / Codebeamer / RQM mapping + 503 retry |
| `test_api_and_workflow.py` | `/health`, PR validate, matrix generate, nightly path |

```bash
pytest -m integration
```

These tests do **not** call real ALM systems.
