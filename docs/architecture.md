# Architecture

Detailed design of the Continuous Traceability Matrix Generator
(**DOORS ↔ Git ↔ RQM ↔ Codebeamer**).

## Goals

| Goal | How the design supports it |
|---|---|
| ASPICE L2/3 bidirectional traceability | Join key = requirement tag across all four systems |
| Low coupling to vendor APIs | Hexagonal ports & adapters |
| Safe merge gates | Deterministic PR validator with explicit issue codes |
| Audit-ready evidence | Nightly HTML/PDF matrix with gap codes |
| Operational resilience | Retries, fail-soft sync, structured logs |

---

## System context

Where this service sits in the automotive toolchain:

```mermaid
flowchart LR
  subgraph Authors
    Eng[Software engineers]
    QA[Validation engineers]
    RE[Requirements engineers]
  end

  subgraph SystemsOfRecord
    DOORS[(IBM DOORS)]
    CB[(Codebeamer)]
    Git[(Git hosting)]
    RQM[(IBM RQM / ETM)]
  end

  subgraph ThisService["Continuous Traceability Matrix Generator"]
    API[REST API]
    CLI[CLI]
    Core[Sync · PR gate · Matrix]
  end

  subgraph Consumers
    PR[PR checks]
    Nightly[Nightly / release CI]
    Audit[ASPICE auditors]
  end

  RE --> DOORS
  Eng --> Git
  Eng --> CB
  QA --> RQM

  DOORS --> Core
  CB --> Core
  Git --> Core
  RQM --> Core

  CLI --> Core
  API --> Core

  Core --> PR
  Core --> Nightly
  Nightly --> Audit
  PR --> Eng
```

---

## Hexagonal (ports & adapters) view

```mermaid
flowchart TB
  subgraph Driving["Driving adapters"]
    CLI[cli.py]
    HTTP[api/ FastAPI]
  end

  subgraph App["Application layer"]
    Sync[SyncService]
    PRV[PRValidatorService]
    Matrix[MatrixGeneratorService]
    Store[(TraceabilityStore)]
  end

  subgraph Domain["Domain"]
    Models[Pydantic models]
    Tags[RequirementTagParser]
  end

  subgraph Ports["Ports / protocols"]
    RP[RequirementsPort]
    CP[CodebeamerPort]
    GP[GitPort]
    QP[RqmPort]
  end

  subgraph Driven["Driven adapters"]
    DA[DoorsAdapter]
    CA[CodebeamerAdapter]
    GA[GitAdapter]
    RA[RqmAdapter]
    HEX[HtmlExporter]
    PEX[PdfExporter]
  end

  CLI --> Sync
  CLI --> PRV
  CLI --> Matrix
  HTTP --> Sync
  HTTP --> PRV
  HTTP --> Matrix

  Sync --> Store
  Sync --> RP & CP & GP & QP
  PRV --> GP & RP & QP
  Matrix --> Store
  Matrix --> HEX & PEX

  Sync --> Models
  PRV --> Tags
  Matrix --> Models

  RP --> DA
  CP --> CA
  GP --> GA
  QP --> RA
```

**Dependency rule:** outer layers may depend inward. Domain and services never import concrete HTTP clients.

---

## Component / package map

```mermaid
flowchart LR
  subgraph pkg["src/traceability"]
    direction TB
    cli[cli.py]
    api[api/]
    container[container.py]
    services[services/]
    ports[ports.py]
    adapters[adapters/]
    domain[domain/]
    exporters[exporters/]
    resilience[resilience/]
    config[config.py]
  end

  cli --> container
  api --> container
  container --> services
  container --> adapters
  container --> exporters
  container --> config
  services --> ports
  services --> domain
  adapters --> ports
  adapters --> resilience
  adapters --> domain
  exporters --> domain
```

| Path | Responsibility |
|---|---|
| `domain/` | Immutable models, tag parsing — no I/O |
| `ports.py` | `Protocol` interfaces for ALM systems |
| `adapters/` | REST clients implementing ports |
| `services/` | Sync, PR validation, matrix generation |
| `exporters/` | HTML / PDF rendering |
| `resilience/` | Retry helpers (tenacity) |
| `api/` | FastAPI routes + schemas |
| `container.py` | Composition root (wiring) |
| `cli.py` | Click commands for CI |
| `config.py` | YAML + env settings |

---

## Domain model (traceability graph)

```mermaid
erDiagram
  REQUIREMENT ||--o{ TRACE_LINK : "target of"
  CODE_ITEM ||--o{ TRACE_LINK : "satisfies"
  GIT_COMMIT ||--o{ TRACE_LINK : "implements"
  RQM_TEST_CASE ||--o{ TRACE_LINK : "verifies"
  RQM_TEST_CASE ||--o{ RQM_EXECUTION : "has runs"
  REQUIREMENT ||--o{ TRACE_ROW : "summarized as"
  TRACEABILITY_MATRIX ||--|{ TRACE_ROW : "contains"

  REQUIREMENT {
    string id
    string tag PK
    string title
    string source
  }
  CODE_ITEM {
    string id PK
    string title
    string item_type
  }
  GIT_COMMIT {
    string sha PK
    string message
    datetime committed_at
  }
  RQM_TEST_CASE {
    string id PK
    string name
    string level
  }
  RQM_EXECUTION {
    string id PK
    string status
    datetime executed_at
    string build_id
  }
  TRACE_LINK {
    string source_id
    string target_id
    string link_type
  }
  TRACE_ROW {
    string requirement_tag
    bool coverage_complete
  }
```

Join key across systems: **requirement tag** (e.g. `REQ_ADAS_USS_042`).

Link types:

| Type | Meaning |
|---|---|
| `satisfies` | Codebeamer item → requirement |
| `implements` | Git commit → requirement |
| `verifies` | RQM test case → requirement |
| `derives` | Child requirement → parent (reserved) |

---

## End-to-end data flow

```mermaid
flowchart LR
  D[DOORS requirements] --> S[SyncService]
  C[Codebeamer items] --> S
  G[Git commits / PRs] --> S
  R[RQM cases + executions] --> S
  S --> Store[(TraceabilityStore)]
  Store --> M[MatrixGenerator]
  M --> HTML[HTML artifact]
  M --> PDF[PDF artifact]

  G2[Git PR] --> V[PRValidator]
  D --> V
  R --> V
  V --> Gate{Compliant?}
  Gate -->|yes| Merge[Allow merge]
  Gate -->|no| Block[Block with issue codes]
```

---

## Sequence: multi-ALM sync

```mermaid
sequenceDiagram
    autonumber
    participant C as CLI / API
    participant S as SyncService
    participant D as DoorsAdapter
    participant CB as CodebeamerAdapter
    participant G as GitAdapter
    participant Q as RqmAdapter
    participant Store as TraceabilityStore

    C->>S: sync_all(branch, build_id)
    S->>Store: clear()
    par Fetch sources
      S->>D: fetch_requirements()
      D-->>S: Requirement[]
      S->>CB: fetch_items()
      CB-->>S: CodeItem[]
      S->>G: fetch_commits(...)
      G-->>S: GitCommit[]
      S->>Q: fetch_test_cases()
      Q-->>S: RqmTestCase[]
      S->>Q: fetch_executions(build_id)
      Q-->>S: RqmExecution[]
    end
    Note over S: On source failure: log + collect error<br/>(unless fail_fast)
    S->>Store: upsert artifacts
    S->>S: _build_links()
    S->>Store: links[]
    S-->>C: SyncResult
```

---

## Sequence: PR compliance gate

```mermaid
sequenceDiagram
    autonumber
    participant CI as PR workflow
    participant V as PRValidatorService
    participant G as GitPort
    participant D as RequirementsPort
    participant Q as RqmPort

    CI->>V: validate(pr_number)
    V->>G: fetch_pull_request(n)
    G-->>V: PullRequest + commits
    V->>V: extract REQ_* tags
    alt no tags
      V-->>CI: MISSING_REQ_TAG (exit 2)
    else tags found
      loop each tag
        V->>D: get_requirement_by_tag(tag)
        D-->>V: Requirement | None
        V->>Q: fetch_test_cases_for_requirement(tag)
        Q-->>V: RqmTestCase[]
        V->>V: require unit/integration level
      end
      V-->>CI: PRValidationResult
    end
```

---

## Sequence: nightly matrix

```mermaid
sequenceDiagram
    participant CI as Nightly CI
    participant CLI as traceability CLI
    participant Sync as SyncService
    participant ALM as DOORS/CB/Git/RQM
    participant Matrix as MatrixGenerator
    participant Exp as HTML/PDF Exporter

    CI->>CLI: generate-matrix --build-id
    CLI->>Sync: sync_all(build_id)
    Sync->>ALM: fetch artifacts (retried)
    ALM-->>Sync: requirements, items, commits, tests
    Sync-->>CLI: SyncResult + store
    CLI->>Matrix: generate(build_id)
    Matrix-->>CLI: TraceabilityMatrix
    CLI->>Exp: write HTML/PDF
    Exp-->>CI: artifacts/
```

---

## Coverage completeness decision

```mermaid
flowchart TD
  Start[TraceRow for requirement tag] --> CB{Codebeamer link?}
  CB -->|no| G1[gap: missing_codebeamer_link]
  CB -->|yes| Git{Git commit?}
  Git -->|no| G2[gap: missing_git_implementation]
  Git -->|yes| TC{RQM test case?}
  TC -->|no| G3[gap: missing_test_case]
  TC -->|yes| EX{Latest execution?}
  EX -->|no| G4[gap: missing_test_execution]
  EX -->|yes| ST{Status failed/blocked?}
  ST -->|yes| G5[gap: failing_or_blocked_execution]
  ST -->|no| OK[coverage_complete = true]
  G1 --> INC[coverage_complete = false]
  G2 --> INC
  G3 --> INC
  G4 --> INC
  G5 --> INC
```

---

## Deployment / runtime topology

```mermaid
flowchart TB
  subgraph CI["CI runners"]
    PRJob[PR gate job]
    NightJob[Nightly matrix job]
  end

  subgraph Optional["Optional long-running service"]
    Uvi[uvicorn + FastAPI]
  end

  subgraph Secrets["Secrets / config"]
    Env[.env / CI secrets]
    Yaml[config/*.yaml]
  end

  subgraph External["Corporate network"]
    DOORS
    CB[Codebeamer]
    GitHub[Git API]
    RQM
  end

  Artifacts[(artifacts/ HTML PDF)]

  PRJob --> CLI1[traceability validate-pr]
  NightJob --> CLI2[traceability generate-matrix]
  CLI2 --> Artifacts
  Uvi --> Services[Services]
  CLI1 --> Services
  CLI2 --> Services
  Env --> CLI1 & CLI2 & Uvi
  Yaml --> CLI1 & CLI2 & Uvi
  Services --> DOORS & CB & GitHub & RQM
```

Typical modes:

1. **Ephemeral CI** — CLI only (recommended for PR gate + nightly)  
2. **Always-on API** — `traceability serve` behind an internal gateway  

---

## Resilience & error model

```mermaid
flowchart LR
  Req[Adapter request] --> Try{Attempt}
  Try -->|network / 408 429 5xx| Wait[Backoff + jitter]
  Wait --> Try
  Try -->|401 403| Auth[AuthenticationError]
  Try -->|404| NF[NotFoundError]
  Try -->|other 4xx| Hard[AdapterError non-retryable]
  Try -->|200| OK[Domain mapping]
```

| Concern | Behavior |
|---|---|
| Retries | `resilience.with_retries` + tenacity |
| Sync failure mode | Fail-soft by default (`sync.fail_fast: false`) |
| Logging | JSON via structlog (`adapter_retry`, `sync_completed`, …) |
| Exceptions | Typed hierarchy in `exceptions.py` |

---

## Design principles (SOLID)

| Principle | Manifestation |
|---|---|
| **S**ingle Responsibility | One service per use-case |
| **O**pen/Closed | New Git provider → new adapter, same `GitPort` |
| **L**iskov | Fakes in tests substitute real adapters |
| **I**nterface Segregation | Narrow ports per system |
| **D**ependency Inversion | Services depend on protocols, not HTTP |

---

## Persistence note

`TraceabilityStore` is intentionally **in-memory**. For multi-instance production, introduce a repository (Postgres/SQLite) behind the same service APIs — exporters and PR validation stay unchanged.

---

## Related docs

- [Data model details](data-model.md)
- [Adapters / JSON façades](adapters.md)
- [Deployment & operations](deployment.md)
- [API](api.md) · [CLI](cli.md) · [CI/CD](ci-cd.md)
