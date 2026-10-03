# Unit tests

Fast tests with **no network**. Services use fakes from `tests/fakes.py`.

| File | Focus |
|---|---|
| `test_requirement_tag.py` | Tag validation / extraction / commit headers |
| `test_matrix_generator.py` | Coverage completeness and gap codes |
| `test_pr_validator.py` | PR gate compliance and error codes |
| `test_sync_service.py` | Link construction and fail-soft sync |
| `test_html_exporter.py` | HTML artifact content |

```bash
pytest -m unit
```
