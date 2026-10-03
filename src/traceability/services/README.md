# Services package

Application use-cases. Each service depends on **ports**, never on concrete adapters.

| Module | Class | Use-case |
|---|---|---|
| `sync_service.py` | `SyncService`, `TraceabilityStore` | Pull ALM data + build links |
| `pr_validator.py` | `PRValidatorService` | PR tag + RQM coverage gate |
| `matrix_generator.py` | `MatrixGeneratorService` | ASPICE matrix + gap analysis |

## `TraceabilityStore`

In-memory aggregate used after sync. Replace with a persistent repository for multi-instance deployments without changing exporters.

## Gap codes (matrix)

Emitted on incomplete rows:

- `missing_codebeamer_link`
- `missing_git_implementation`
- `missing_test_case`
- `missing_test_execution`
- `failing_or_blocked_execution`

## Related docs

- [CLI](../../../docs/cli.md)
- [Architecture](../../../docs/architecture.md)
- [Requirement tags](../../../docs/requirement-tags.md)
