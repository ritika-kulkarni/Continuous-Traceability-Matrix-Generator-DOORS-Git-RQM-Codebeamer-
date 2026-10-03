# Config

Runtime configuration for the traceability service.

| File | Purpose |
|---|---|
| `default.yaml` | Checked-in defaults for local / CI baselines |

## Usage

```bash
traceability --config config/default.yaml sync
```

Override with environment variables (see [docs/configuration.md](../docs/configuration.md) and [`.env.example`](../.env.example)).

## Recommended practice

1. Keep `default.yaml` non-secret and safe to commit  
2. Put credentials only in env / CI secrets  
3. Add environment-specific overlays (e.g. `config/prod.yaml`) as needed — do not commit secrets into overlays either  
