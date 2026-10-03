# Adapters

Adapters translate vendor REST APIs into domain models. Services never call HTTP directly.

## Implemented adapters

| Adapter | Port | Default auth | Notes |
|---|---|---|---|
| `DoorsAdapter` | `RequirementsPort` | Basic | Module-scoped requirements list/lookup |
| `CodebeamerAdapter` | `CodebeamerPort` | Bearer token | Project items + requirement tags |
| `GitAdapter` | `GitPort` | Bearer token | GitHub-compatible REST |
| `RqmAdapter` | `RqmPort` | Basic | Test cases + executions |

Shared HTTP behavior lives in `adapters/http_base.py` (timeouts, auth errors, retries).

## Expected JSON façades

Real DOORS DWA / RQM OSLC payloads differ by version. Adapters assume a **thin JSON façade**. Map your deployment to these shapes (API gateway, proxy, or adapter field remapping).

### DOORS — `GET /requirements`

```json
{
  "items": [
    {
      "id": "D-100",
      "tag": "REQ_ADAS_USS_042",
      "title": "Ultrasonic obstacle detection within 2m",
      "description": "...",
      "status": "Approved",
      "module": "/ADAS/USS",
      "parentId": null,
      "lastModified": "2026-03-01T10:00:00+00:00",
      "attributes": {}
    }
  ]
}
```

Query params: `module`, `tag`.

### Codebeamer — `GET /projects/{id}/items`

```json
{
  "items": [
    {
      "id": "CB-501",
      "name": "USS ranging SW design",
      "type": "Design",
      "status": "In Progress",
      "requirementTags": ["REQ_ADAS_USS_042"],
      "requirementIds": ["D-100"],
      "uri": "https://codebeamer.example/item/501"
    }
  ]
}
```

### GitHub — PR + commits

Uses standard GitHub REST:

- `GET /repos/{owner}/{repo}/pulls/{number}`
- `GET /repos/{owner}/{repo}/pulls/{number}/commits`
- `GET /repos/{owner}/{repo}/commits`

Requirement tags are parsed from commit messages.

### RQM — test cases / executions

```json
{
  "items": [
    {
      "id": "TC-900",
      "name": "USS unit: range accuracy",
      "level": "unit",
      "requirementTags": ["REQ_ADAS_USS_042"],
      "scriptPath": "tests/unit/uss_range.c"
    }
  ]
}
```

```json
{
  "items": [
    {
      "id": "EX-1",
      "testCaseId": "TC-900",
      "status": "passed",
      "executedAt": "2026-03-02T00:00:00Z",
      "buildId": "nightly-42",
      "logUrl": "https://rqm.example/logs/EX-1"
    }
  ]
}
```

## Adding a new Git provider

1. Implement `GitPort` (`fetch_pull_request`, `fetch_commits`)  
2. Register it in `container.py` based on `git.provider`  
3. Add integration tests with `respx`  
4. Keep tag extraction via `RequirementTagParser`  

`GitAdapter` currently raises if `provider != github` to avoid silent wrong API paths.

## Adapting field names

Prefer small private mappers inside the adapter:

```python
def _to_requirement(self, item: dict[str, Any]) -> Requirement:
    raw_tag = item.get("customReqId") or item.get("tag")
    ...
```

Do **not** leak vendor field names into `services/` or `domain/`.

## Resilience

All adapters use `with_retries`:

- Exponential backoff + jitter  
- Retries on network errors and selected HTTP statuses  
- Structured `adapter_retry` log events  

Tune via `*_settings.max_retries` and `timeout_seconds`.

## Testing adapters

See `tests/integration/test_adapters_http.py` for `respx`-mocked happy paths and a 503→200 retry case.
