# Configuration

Configuration is loaded from YAML and overridden by environment variables.

## Load order

1. `config/default.yaml` (or path passed via `--config`)  
2. Convenience secret env vars (`DOORS_PASSWORD`, `GIT_TOKEN`, …)  
3. Nested `TRACEABILITY__*` settings (pydantic-settings)  

```bash
traceability --config config/default.yaml sync
```

## File: `config/default.yaml`

Top-level sections:

| Section | Purpose |
|---|---|
| `app` | Service name, environment, log level, tag regex |
| `doors` | DOORS REST base URL, auth, module path, retries |
| `codebeamer` | CB REST base URL, token, project id |
| `git` | Provider, API base, owner/repo, token |
| `rqm` | RQM integration service URL, project area |
| `matrix` | Output directory, title, orphan inclusion, template |
| `sync` | Batch size, fail-fast flag |

## Environment variables

### Secrets (preferred)

| Variable | Maps to |
|---|---|
| `DOORS_PASSWORD` | `doors.password` |
| `CODEBEAMER_TOKEN` | `codebeamer.token` |
| `GIT_TOKEN` | `git.token` |
| `RQM_PASSWORD` | `rqm.password` |

### Nested overrides

Pattern: `TRACEABILITY__<SECTION>__<FIELD>`

Examples:

```bash
export TRACEABILITY__APP__LOG_LEVEL=DEBUG
export TRACEABILITY__GIT__OWNER=adas-org
export TRACEABILITY__GIT__REPO=uss-firmware
export TRACEABILITY__GIT__PROVIDER=github
export TRACEABILITY__MATRIX__OUTPUT_DIR=/var/aspice/artifacts
export TRACEABILITY__SYNC__FAIL_FAST=true
export TRACEABILITY__DOORS__MODULE_PATH=/Project/ADAS/Requirements
```

Boolean/int values are parsed by pydantic.

## Requirement tag pattern

Default:

```yaml
app:
  req_tag_pattern: "REQ_[A-Z0-9]+(?:_[A-Z0-9]+)*_\\d{3,}"
```

Override only if your organization uses a different ID scheme — and update developer docs / PR templates accordingly.

## Example project overlay

`config/prod.yaml` (illustrative):

```yaml
app:
  environment: production
  log_level: INFO

doors:
  base_url: https://doors.corp.example/dwa/api
  username: svc_traceability
  module_path: /ADAS/SystemRequirements
  max_retries: 5

git:
  provider: github
  base_url: https://api.github.com
  owner: adas-org
  repo: ecu-firmware

matrix:
  output_dir: /data/aspice/matrices
  title: "ADAS ASPICE Traceability Matrix"
```

```bash
traceability --config config/prod.yaml generate-matrix --build-id "$BUILD_ID"
```

## Secrets hygiene

- Never commit `.env` or real tokens  
- Use `.env.example` as the template  
- Prefer CI secrets (`GitHub Actions secrets`) for PR gate / nightly jobs  
- Treat Codebeamer / Git tokens as least-privilege read scopes  

## Validation

Invalid YAML or missing config file raises `ConfigurationError` at startup. Adapter auth failures surface as `AuthenticationError` during the first request.
