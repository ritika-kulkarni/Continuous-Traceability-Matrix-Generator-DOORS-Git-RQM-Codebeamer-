# Contributing

Thanks for improving ASPICE traceability automation.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
```

See [getting-started.md](getting-started.md) and [testing.md](testing.md).

## Coding standards

- Prefer clear names over comments that restate code  
- Keep business rules in `services/`; keep HTTP in `adapters/`  
- Domain models stay I/O-free and preferably frozen  
- Use structured logging (`get_logger`), not print  
- Match existing typing (Python 3.11+ syntax)  
- Line length 100 (ruff)  

## Architecture rules

1. **Do not** import adapters from domain  
2. **Do not** put vendor JSON field names in services  
3. New external systems → new port + adapter + tests  
4. Wire new components in `container.py`  

## Commit & PR guidelines

- Use requirement tags when the change implements a tracked requirement:

  ```text
  feat: add orphan-test filter

  Requires: REQ_TOOL_TRACE_001
  ```

- Include unit or integration tests for behavior changes  
- Update docs when CLI/API/config contracts change  
- Keep PRs focused  

### Pre-submit checklist

- [ ] `pytest` passes  
- [ ] `ruff check src tests` passes  
- [ ] Docs updated if user-facing behavior changed  
- [ ] No secrets in the diff  
- [ ] New adapter fields documented in [adapters.md](adapters.md)  

## Documentation

- User-facing guides live under `docs/`  
- Package READMEs stay short (purpose + entry points + links)  
- Root `README.md` is the landing page — keep it skim-friendly  

## Reporting issues

Include:

- Python version  
- Command / endpoint invoked  
- Redacted config sections  
- Full error JSON or log snippet  
