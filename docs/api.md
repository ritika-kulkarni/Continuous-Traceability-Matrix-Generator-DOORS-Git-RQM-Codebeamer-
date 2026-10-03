# REST API

Base URL (local default): `http://127.0.0.1:8080`

Interactive docs:

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
- ReDoc: `/redoc`

## Authentication

The service itself does not implement end-user auth in the open-source scaffold. Protect it at the edge (API gateway, mTLS, VPN) in production. Outbound ALM credentials come from server-side config/env.

## Endpoints

### `GET /health`

Liveness probe.

**Response `200`**

```json
{
  "status": "ok",
  "service": "ASPICE Traceability Matrix Generator",
  "version": "1.0.0"
}
```

---

### `POST /api/v1/sync`

Synchronize DOORS ↔ Codebeamer ↔ Git ↔ RQM.

**Request**

```json
{
  "git_since": "2026-01-01T00:00:00Z",
  "git_branch": "main",
  "build_id": "nightly-42"
}
```

All fields optional.

**Response `200`**

```json
{
  "result": {
    "requirements_synced": 120,
    "code_items_synced": 85,
    "commits_synced": 40,
    "tests_synced": 200,
    "links_created": 310,
    "errors": [],
    "started_at": "2026-03-15T02:00:00Z",
    "finished_at": "2026-03-15T02:01:12Z"
  }
}
```

**Errors**

| Status | When |
|---|---|
| `502` | Adapter failure in fail-fast scenarios / hard transport errors |

---

### `POST /api/v1/pr/validate`

Validate requirement tags and RQM coverage for a PR.

**Request**

```json
{
  "pr_number": 42
}
```

**Response `200`**

```json
{
  "result": {
    "pr_number": 42,
    "compliant": false,
    "tags_found": ["REQ_ADAS_USS_042"],
    "issues": [
      {
        "severity": "error",
        "code": "MISSING_TEST_CASE",
        "message": "No RQM test case linked to 'REQ_ADAS_USS_042'.",
        "requirement_tag": "REQ_ADAS_USS_042"
      }
    ],
    "validated_at": "2026-03-15T10:00:00Z"
  }
}
```

**Errors**

| Status | When |
|---|---|
| `404` | PR not found |
| `502` | Upstream ALM error |

---

### `POST /api/v1/matrix/generate`

Optionally sync, then generate and export the matrix.

**Request**

```json
{
  "build_id": "nightly-42",
  "sync_first": true,
  "git_since": null,
  "git_branch": "main",
  "export_html": true,
  "export_pdf": false
}
```

**Response `200`**

```json
{
  "matrix": {
    "title": "ASPICE Bidirectional Traceability Matrix",
    "generated_at": "2026-03-15T02:05:00Z",
    "build_id": "nightly-42",
    "rows": [],
    "orphan_requirements": [],
    "orphan_tests": [],
    "summary": {
      "requirements_total": 120,
      "rows_complete": 110,
      "rows_with_gaps": 10,
      "orphan_requirements": 10,
      "orphan_tests": 3,
      "links": 310
    }
  },
  "html_path": "artifacts/traceability_matrix_20260315T020500Z.html",
  "pdf_path": null,
  "generated_at": "2026-03-15T02:05:00Z"
}
```

**Errors**

| Status | When |
|---|---|
| `500` | Export / domain failure (`TraceabilityError`) |

## curl examples

```bash
curl -s http://127.0.0.1:8080/health | jq

curl -s -X POST http://127.0.0.1:8080/api/v1/pr/validate \
  -H 'Content-Type: application/json' \
  -d '{"pr_number":42}' | jq

curl -s -X POST http://127.0.0.1:8080/api/v1/matrix/generate \
  -H 'Content-Type: application/json' \
  -d '{"build_id":"nightly-1","sync_first":true,"export_html":true,"export_pdf":false}' | jq
```
