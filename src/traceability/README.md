# `traceability` package

Application root for the ASPICE Continuous Traceability Matrix Generator.

## Entry points

| Entry | Module | Purpose |
|---|---|---|
| CLI | `traceability.cli:main` | `sync`, `validate-pr`, `generate-matrix`, `serve` |
| API app | `traceability.api.app:app` | FastAPI ASGI application |
| Composition | `traceability.container.build_container` | Wire settings → adapters → services |

## Layout

```text
traceability/
├── domain/        # Models + tag rules
├── adapters/      # DOORS, Codebeamer, Git, RQM
├── services/      # Sync, PR gate, matrix
├── exporters/     # HTML / PDF
├── api/           # REST surface
├── resilience/    # Retries
├── config.py      # Settings
├── container.py   # DI / composition root
├── ports.py       # Protocols
├── exceptions.py  # Error taxonomy
├── logging_setup.py
└── cli.py
```

## Design rule

Depend **inward**: `api` / `cli` → `services` → `ports` ← `adapters`.  
Never import adapters from `domain`.

## Docs

- [Architecture](../../docs/architecture.md)
- [Getting started](../../docs/getting-started.md)
- [API](../../docs/api.md)
- [CLI](../../docs/cli.md)
