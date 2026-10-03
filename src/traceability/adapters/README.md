# Adapters package

Concrete REST clients that implement ports defined in `traceability.ports`.

| Module | Class | System |
|---|---|---|
| `doors.py` | `DoorsAdapter` | IBM DOORS |
| `codebeamer.py` | `CodebeamerAdapter` | Codebeamer |
| `git_client.py` | `GitAdapter` | GitHub-compatible Git hosting |
| `rqm.py` | `RqmAdapter` | IBM RQM / ETM |
| `http_base.py` | `HttpAdapterBase` | Shared httpx + retries |

## Responsibilities

- Authenticate and call vendor APIs  
- Map JSON → domain models  
- Raise typed `AdapterError` / `AuthenticationError` / `NotFoundError`  
- Retry transient failures via `resilience.with_retries`  

## Not allowed here

- ASPICE business rules (those belong in `services/`)  
- HTML/PDF rendering  
- CLI / FastAPI concerns  

## Extending

See [docs/adapters.md](../../../docs/adapters.md) for expected JSON façades and how to add GitLab/Azure providers.
