# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Production readiness review document
- Contributing guidelines
- CHANGELOG.md

### Changed
- Updated README with version compatibility matrix

---

## [0.1.1] - 2026-01-22

### Added
- Comprehensive test suite with 70% code coverage
  - `test_migration/` - Migration script tests
  - `test_postgres/` - PostgreSQL helper tests
  - `test_security/` - Security validation (SQL injection, credential handling)
  - `test_validation/` - App spec and configuration validation
  - `test_edge_cases/` - Edge case and error handling tests
  - `test_workflows/` - End-to-end workflow tests
  - `test_shared/` - Shared configuration tests
- CI/CD pipeline with GitHub Actions (`test.yml`, `ci.yml`)
  - Multi-OS matrix (Ubuntu, macOS)
  - Multi-Python matrix (3.11, 3.12, 3.13)
  - Codecov integration for coverage reporting
- Test infrastructure files
  - `pytest.ini` - pytest configuration
  - `requirements-dev.txt` - development dependencies
  - `conftest.py` - shared test fixtures

### Security
- Added credential pattern documentation
- Added security scanning in CI
- Security tests for SQL injection prevention
- Credential handling validation tests

---

## [0.1.0] - 2026-01-22

### Added
- Initial release with 11 specialized skills:
  - `designer` - Natural language to App Spec
  - `deployment` - GitHub Actions CI/CD
  - `migration` - Platform migration
  - `postgres` - PostgreSQL configuration
  - `managed-db-services` - MySQL, MongoDB, Valkey, Kafka
  - `networking` - Domains, routing, CORS, VPC
  - `spaces` - S3-compatible storage
  - `ai-services` - Gradient AI inference
  - `troubleshooting` - Debug and diagnostics
  - `devcontainers` - Local development
  - `sandbox` - Isolated execution
  - `planner` - Staged project planning
- Shared configuration files
- Python helper scripts
- Architecture documentation

### Notes
- Pre-release for internal testing
- Container images on personal account (to be migrated)
