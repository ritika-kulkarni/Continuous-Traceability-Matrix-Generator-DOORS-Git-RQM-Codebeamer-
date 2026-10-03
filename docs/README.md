# Documentation index

Welcome to the Continuous Traceability Matrix Generator docs.

This project links **IBM DOORS**, **Codebeamer**, **Git**, and **IBM RQM** into a bidirectional ASPICE traceability graph and exports audit-ready matrices.

## Start here

1. [Getting started](getting-started.md) — install and run your first sync  
2. [Architecture](architecture.md) — how the codebase is structured  
3. [Configuration](configuration.md) — YAML and environment overrides  

## Operator guides

| Document | Audience | Contents |
|---|---|---|
| [CLI reference](cli.md) | CI / release engineers | Command flags and exit codes |
| [REST API](api.md) | Integrators | Endpoints and JSON schemas |
| [Requirement tags](requirement-tags.md) | Developers | Tag format and PR conventions |
| [CI/CD](ci-cd.md) | DevOps | GitHub Actions wiring |
| [Troubleshooting](troubleshooting.md) | Support / on-call | Common failures |

## Extender guides

| Document | Audience | Contents |
|---|---|---|
| [Adapters](adapters.md) | Platform engineers | Map real ALM API payloads |
| [Testing](testing.md) | Contributors | How to run and extend tests |
| [Contributing](contributing.md) | Contributors | Coding standards and PR checklist |

## Package-level READMEs

Each major package has a short README describing responsibility and public entry points:

- [`src/traceability/`](../src/traceability/README.md)
- [`src/traceability/domain/`](../src/traceability/domain/README.md)
- [`src/traceability/adapters/`](../src/traceability/adapters/README.md)
- [`src/traceability/services/`](../src/traceability/services/README.md)
- [`src/traceability/api/`](../src/traceability/api/README.md)
- [`src/traceability/exporters/`](../src/traceability/exporters/README.md)
- [`tests/`](../tests/README.md)
- [`config/`](../config/README.md)
- [`scripts/`](../scripts/README.md)
- [`.github/workflows/`](../.github/workflows/README.md)

## Glossary

| Term | Meaning |
|---|---|
| **ASPICE** | Automotive SPICE — process assessment model requiring bidirectional requirements traceability |
| **Requirement tag** | Stable ID such as `REQ_ADAS_USS_042` carried in commits, design items, and tests |
| **Trace row** | One requirement’s end-to-end coverage status in the matrix |
| **Gap** | Missing link (design, commit, test case, or execution evidence) |
| **Port** | Interface that an adapter implements (Dependency Inversion) |
| **Adapter** | Concrete REST client for an ALM tool |
