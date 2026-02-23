# Operations Runbook

## Maintainer Responsibilities

- Keep core skills current with App Platform capabilities.
- Ensure tests and validation remain green.
- Triage issues and pull requests with SLA discipline.
- Maintain documentation consistency across root docs and `Docs/`.

## Routine Maintenance Cadence

### Daily / Per PR

- Review CI signal
- Triage new issues
- Validate quality gates for merged PRs

### Weekly

- Dependency hygiene (`requirements-dev.txt`)
- Review flaky test patterns
- Review open security concerns

### Monthly

- Confirm tool/version guidance remains accurate
- Audit shared defaults and region/instance references
- Review docs for staleness

## Incident Response (Repository Scope)

For critical regressions/security findings:

1. Open incident issue with severity and blast radius.
2. Reproduce with minimal failing test.
3. Patch in smallest safe diff.
4. Add regression test.
5. Verify affected suites and publish mitigation notes.

## Quality Escalation Rules

Escalate to maintainers when:

- security-sensitive behavior changes without tests
- schema validation is bypassed or disabled
- release process diverges from documented policy

## CI / Local Health Commands

```bash
make test
make test-cov
make test-security
python scripts/validate_skills.py
```

## Analytics and Observability Notes

Repository-level analytics assets live under `analytics/` and scripts in `scripts/collect_analytics.py` and `scripts/view_analytics.py`.

Treat analytics artifacts as operational signals, not source-of-truth policy definitions.
