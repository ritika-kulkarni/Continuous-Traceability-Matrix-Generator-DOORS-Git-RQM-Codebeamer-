# CI/CD integration

Three GitHub Actions workflows ship with the project.

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | push / PR | Lint + pytest |
| PR gate | `.github/workflows/pr-traceability-gate.yml` | pull_request | Tag + RQM validation |
| Nightly matrix | `.github/workflows/nightly-matrix.yml` | cron / manual | HTML/PDF artifact |

See also [.github/workflows/README.md](../.github/workflows/README.md).

## Required GitHub configuration

### Secrets

| Secret | Used by |
|---|---|
| `DOORS_PASSWORD` | PR gate, nightly |
| `CODEBEAMER_TOKEN` | PR gate, nightly |
| `GIT_TOKEN` | PR gate, nightly (repo metadata) |
| `RQM_PASSWORD` | PR gate, nightly |

### Variables (repository or org)

| Variable | Example |
|---|---|
| `DOORS_BASE_URL` | `https://doors.corp/dwa/api` |
| `DOORS_USERNAME` | `svc_traceability` |
| `CODEBEAMER_BASE_URL` | `https://cb.corp/cb/rest` |
| `RQM_BASE_URL` | `https://rqm.corp/.../IMainService` |
| `RQM_USERNAME` | `svc_traceability` |

## PR gate behavior

On each PR open/sync:

```bash
traceability validate-pr ${{ github.event.pull_request.number }}
```

- Exit `0` → check green  
- Exit `2` → check red (non-compliant tags/tests)  

Developers see JSON issue codes in the job log (`MISSING_REQ_TAG`, etc.).

## Nightly matrix behavior

```bash
bash scripts/nightly_matrix.sh
```

Artifacts under `artifacts/` are uploaded via `actions/upload-artifact`.

Optional: publish HTML to an internal static site or attach to a release.

## Jenkins / Azure DevOps / GitLab

The CLI is CI-agnostic. Minimal pipeline stage:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[pdf]"
export BUILD_ID="nightly-$(date -u +%Y%m%d)"
traceability --config config/default.yaml generate-matrix \
  --build-id "$BUILD_ID" --html --pdf
```

For merge requests:

```bash
traceability validate-pr "$CI_MERGE_REQUEST_IID"
```

(Adjust the PR number variable for your platform; GitLab may need API mapping if IDs differ from GitHub.)

## Quality gates (recommended)

| Stage | Gate |
|---|---|
| PR | `validate-pr` must exit 0 |
| Nightly | Archive matrix even if exit 3; open defect if `rows_with_gaps` rises |
| Release | Require `rows_with_gaps == 0` for the release build id |

## Branch protection

Enable required status checks:

1. `ci / test`  
2. `pr-traceability-gate / validate-requirement-tags`  
