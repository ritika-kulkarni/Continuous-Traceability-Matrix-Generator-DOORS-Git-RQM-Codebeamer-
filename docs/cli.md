# CLI reference

Entry point: `traceability` (Click group).

```bash
traceability [GLOBAL OPTIONS] COMMAND [ARGS]
```

## Global options

| Option | Description |
|---|---|
| `--config PATH` | YAML config file (must exist) |
| `--log-level LEVEL` | Override `app.log_level` (`DEBUG`, `INFO`, …) |

## Commands

### `sync`

Pull artifacts from all ALM systems and build links.

```bash
traceability sync [--git-since ISO8601] [--git-branch NAME] [--build-id ID]
```

| Flag | Description |
|---|---|
| `--git-since` | Only commits after this timestamp |
| `--git-branch` | Branch / SHA tip to list commits from |
| `--build-id` | Filter RQM executions for this build |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Sync finished with no per-source errors |
| `1` | One or more sources failed (fail-soft mode) |

Stdout: JSON `SyncResult`.

---

### `validate-pr`

ASPICE PR compliance gate.

```bash
traceability validate-pr PR_NUMBER
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Compliant |
| `2` | Non-compliant (missing/invalid tags or tests) |

Stdout: JSON `PRValidationResult` including `tags_found` and `issues[]`.

Issue codes:

| Code | Severity | Meaning |
|---|---|---|
| `MISSING_REQ_TAG` | error | No tags in PR title/body/commits |
| `INVALID_REQ_TAG` | error | Tag fails regex |
| `UNKNOWN_REQUIREMENT` | error | Tag not in DOORS |
| `MISSING_TEST_CASE` | error | No RQM case for tag |
| `MISSING_UNIT_OR_INTEGRATION_TEST` | error | Only system/acceptance cases found |

---

### `generate-matrix`

Sync (unless skipped) and export the ASPICE matrix.

```bash
traceability generate-matrix \
  [--build-id ID] \
  [--git-since ISO8601] \
  [--git-branch NAME] \
  [--skip-sync] \
  [--pdf/--no-pdf] \
  [--html/--no-html] \
  [--output-dir DIR]
```

| Flag | Default | Description |
|---|---|---|
| `--build-id` | none | Stamp + RQM execution filter |
| `--skip-sync` | false | Use existing in-process store only (rarely useful in CLI) |
| `--html / --no-html` | html on | Write HTML artifact |
| `--pdf / --no-pdf` | pdf on | Write PDF (requires `[pdf]` extra) |
| `--output-dir` | `matrix.output_dir` | Destination directory |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | All requirement rows complete |
| `3` | Matrix written but gaps remain |

Stdout: JSON summary with artifact paths.

---

### `serve`

Run the FastAPI sync service.

```bash
traceability serve [--host 0.0.0.0] [--port 8080]
```

See [api.md](api.md).

## CI examples

```bash
# PR check
traceability validate-pr "$PR_NUMBER"

# Nightly
traceability generate-matrix --build-id "nightly-$DATE" --html --pdf
```

Or use `scripts/nightly_matrix.sh` — see [scripts/README.md](../scripts/README.md).
