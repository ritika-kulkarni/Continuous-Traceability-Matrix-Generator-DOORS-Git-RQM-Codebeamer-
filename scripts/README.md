# Scripts

Operational helpers for release / nightly pipelines.

| Script | Purpose |
|---|---|
| `nightly_matrix.sh` | Sync + generate HTML/PDF matrix for a build |

## `nightly_matrix.sh`

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `TRACEABILITY_CONFIG` | `config/default.yaml` | Config path |
| `BUILD_ID` | `nightly-YYYYMMDD` | Build stamp / RQM filter |
| `OUTPUT_DIR` | `artifacts` | Export directory |
| `GIT_BRANCH` | `main` | Branch for commit fetch |

```bash
chmod +x scripts/nightly_matrix.sh
export BUILD_ID=nightly-20260315
bash scripts/nightly_matrix.sh
```

Requires the `traceability` CLI on `PATH` (activate your venv first).

See [docs/ci-cd.md](../docs/ci-cd.md).
