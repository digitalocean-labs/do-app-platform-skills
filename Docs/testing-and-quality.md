# Testing and Quality Strategy

## Quality Objectives

- Prevent regressions in skill behavior and helper scripts.
- Enforce security-safe implementation patterns.
- Keep changes fast to validate locally and in CI.

## Test Topology

Primary suites (under `tests/`):

- `test_migration/`
- `test_postgres/`
- `test_security/`
- `test_validation/`
- `test_workflows/`
- `test_shared/`
- `test_edge_cases/`

## Command Reference

```bash
# all tests
pytest

# full postgres suite
pytest -q tests/test_postgres

# security-focused
pytest -q tests/test_security

# schema/validation
pytest -q tests/test_validation
```

## Marker Model

Markers are configured in [pytest.ini](../pytest.ini), including unit, integration, security, validation, and e2e tags.

## Required Quality Gates

For non-trivial changes:

1. Focused suite for changed component
2. Security or validation suite when relevant
3. Full affected domain suite
4. Changelog/doc updates for behavioral changes

## Security Regression Expectations

For sensitive areas (credentials, SQL generation/execution):

- Add tests for both positive and negative cases.
- Assert unsafe patterns are absent where practical.
- Include at least one regression test that would fail if a known vulnerability pattern reappears.

## CI Alignment

CI should mirror local expectations:

- test execution
- schema validation
- lint/quality checks

Use `make ci` for a local approximation of CI behavior.

## Additional Reference

See [TESTING](../TESTING.md) for detailed fixture usage and testing patterns.
