# Resilience package

Retry helpers for flaky ALM HTTP APIs.

| Export | Purpose |
|---|---|
| `with_retries` | Async retry with exponential jitter |

Retryable conditions:

- `AdapterError.retryable is True`
- httpx timeouts / network errors
- HTTP `408`, `425`, `429`, `500`, `502`, `503`, `504`

Used by `adapters.http_base.HttpAdapterBase.request`.

Tune attempts via each system's `max_retries` setting in config.
