# GitHub Actions workflows

| Workflow | File | Purpose |
|---|---|---|
| CI | `ci.yml` | `ruff` + `pytest` on push/PR |
| PR traceability gate | `pr-traceability-gate.yml` | Enforce `REQ_*` tags + RQM coverage |
| Nightly matrix | `nightly-matrix.yml` | Generate and upload ASPICE artifacts |

## Enabling in your org

1. Add repository **secrets** and **variables** listed in [docs/ci-cd.md](../../docs/ci-cd.md)  
2. Point `config/default.yaml` (or a dedicated config) at real ALM URLs  
3. Require the PR gate check in branch protection rules  
4. Confirm nightly artifact upload path `artifacts/`  

## Local equivalents

```bash
# CI
ruff check src tests && pytest --cov=traceability

# PR gate
traceability validate-pr 42

# Nightly
bash scripts/nightly_matrix.sh
```
