# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-10-03

### Added

- Hexagonal Python package linking DOORS, Codebeamer, Git, and RQM  
- CLI: `sync`, `validate-pr`, `generate-matrix`, `serve`  
- FastAPI REST API for sync, PR validation, and matrix export  
- HTML exporter (Jinja2) and optional PDF exporter (WeasyPrint)  
- PR compliance gate for `REQ_*` tags and RQM unit/integration coverage  
- Nightly matrix script and GitHub Actions workflows  
- Unit + integration test suite with fakes and `respx`  
- Documentation set under `docs/` and package-level READMEs  

[1.0.0]: https://github.com/example/traceability-matrix/releases/tag/v1.0.0
