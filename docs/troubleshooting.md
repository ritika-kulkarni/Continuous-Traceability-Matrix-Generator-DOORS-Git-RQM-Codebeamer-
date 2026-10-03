# Troubleshooting

## Install / environment

### `requires a different Python: … not in '>=3.11'`

Use Python 3.11+. On macOS with Homebrew:

```bash
/opt/homebrew/bin/python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### CLI `traceability` not found

Ensure the venv is active and the package was installed editable:

```bash
pip install -e .
which traceability
```

### PDF export fails / WeasyPrint import error

Install the optional extra **and** OS libraries, or generate HTML only:

```bash
traceability generate-matrix --html --no-pdf
```

---

## Configuration

### `ConfigurationError: config file not found`

Pass an absolute/relative path that exists:

```bash
traceability --config config/default.yaml sync
```

### Auth failures (`AuthenticationError` / HTTP 401/403)

- Verify `DOORS_PASSWORD`, `CODEBEAMER_TOKEN`, `GIT_TOKEN`, `RQM_PASSWORD`  
- Confirm tokens have read scope for the target project/repo  
- Check clock skew for token expiry  

---

## Sync

### `requirements_synced: 0` with errors listed

Fail-soft mode captured a source failure. Inspect `SyncResult.errors` and logs for `sync_source_failed`.

Raise severity temporarily:

```bash
export TRACEABILITY__SYNC__FAIL_FAST=true
```

### Empty executions for a known build

`build_id` filters RQM executions. The ID must match what RQM stored (e.g. `nightly-42` vs `nightly-99`).

### Retries exhausting

Look for `adapter_retry` log events. Increase `max_retries` / `timeout_seconds` for the flaky system, or fix upstream availability.

---

## PR validation

### `MISSING_REQ_TAG`

Add a compliant tag to the PR title/body or commit header:

```text
Requires: REQ_ADAS_USS_042
```

### `UNKNOWN_REQUIREMENT`

Tag is well-formed but not returned by DOORS. Confirm module path and that the requirement is approved/exported.

### `MISSING_TEST_CASE` / `MISSING_UNIT_OR_INTEGRATION_TEST`

Create or link an RQM unit/integration case with the same tag. System tests alone do not satisfy the gate.

---

## Matrix

### Exit code `3` after `generate-matrix`

Artifact was written, but some rows have gaps. Open the HTML and inspect the **Gaps** column:

| Gap code | Meaning |
|---|---|
| `missing_codebeamer_link` | No design/work item tag |
| `missing_git_implementation` | No commit with tag |
| `missing_test_case` | No RQM case |
| `missing_test_execution` | Case exists but no execution for build |
| `failing_or_blocked_execution` | Latest run failed/blocked |

### All rows incomplete unexpectedly

Confirm sync actually populated the store (run `sync` first, check counts). For CLI, do not use `--skip-sync` unless you intentionally injected data.

---

## API

### `502` from `/api/v1/sync` or `/pr/validate`

Upstream adapter error. Check service logs (`adapter_retry`, exception message) and ALM health.

### Matrix generate returns `500` on PDF

Disable PDF (`"export_pdf": false`) or install WeasyPrint system deps.

---

## Still stuck?

1. Reproduce with `TRACEABILITY__APP__LOG_LEVEL=DEBUG`  
2. Run the relevant unit/integration test  
3. Capture the JSON result body / log line  
4. Open an issue with config redacted (no secrets)  
