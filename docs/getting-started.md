# Getting started

This guide gets you from a clean clone to a running sync service and a generated matrix.

## Prerequisites

- Python **3.11+** (3.12 / 3.14 recommended)
- Network access to your DOORS, Codebeamer, Git, and RQM endpoints (or use fakes/mocks for local demos)
- Optional for PDF: WeasyPrint system dependencies (Cairo, Pango, GDK-PixBuf)

## 1. Clone and install

```bash
cd "Continuous Traceability Matrix Generator (DOORS ↔ Git ↔ RQM ↔ Codebeamer)"

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -U pip
pip install -e ".[dev]"

# Optional PDF export
pip install -e ".[pdf]"
```

The CLI entry point `traceability` is installed into your virtualenv.

## 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and `config/default.yaml` for your environment. Minimum useful settings:

| Setting | Example |
|---|---|
| `TRACEABILITY__GIT__OWNER` | `my-org` |
| `TRACEABILITY__GIT__REPO` | `ecu-firmware` |
| `GIT_TOKEN` | GitHub PAT with `repo` read |
| `DOORS_PASSWORD` / `CODEBEAMER_TOKEN` / `RQM_PASSWORD` | ALM credentials |

See [configuration.md](configuration.md) for the full reference.

## 3. Verify the install

```bash
pytest
ruff check src tests
traceability --help
```

## 4. Run the API locally

```bash
traceability serve --host 127.0.0.1 --port 8080
```

- Health: `GET http://127.0.0.1:8080/health`
- Swagger UI: `http://127.0.0.1:8080/docs`
- ReDoc: `http://127.0.0.1:8080/redoc`

## 5. First sync (CLI)

```bash
traceability --config config/default.yaml sync \
  --git-branch main \
  --build-id local-demo-1
```

On success you get a JSON `SyncResult` with counts for requirements, code items, commits, tests, and links.

> If an ALM is unreachable, sync **continues** by default and lists errors in the result (`sync.fail_fast: false`).

## 6. Validate a pull request

```bash
traceability validate-pr 42
echo $?   # 0 compliant, 2 non-compliant
```

Rules enforced:

1. At least one valid requirement tag in PR title/body/commits  
2. Tag exists in DOORS (via requirements port)  
3. At least one linked RQM unit or integration test case  

## 7. Generate a matrix artifact

```bash
mkdir -p artifacts
traceability generate-matrix \
  --build-id local-demo-1 \
  --git-branch main \
  --output-dir artifacts \
  --html \
  --no-pdf
```

Open the HTML file under `artifacts/`. Gaps (missing design / commit / test / execution) appear per requirement row.

## 8. Nightly script (release builds)

```bash
export BUILD_ID=nightly-$(date -u +%Y%m%d)
bash scripts/nightly_matrix.sh
```

## Next steps

- Wire CI: [ci-cd.md](ci-cd.md)  
- Map real ALM JSON: [adapters.md](adapters.md)  
- Understand internals: [architecture.md](architecture.md)  
