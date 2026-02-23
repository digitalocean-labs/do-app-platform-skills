# Developer Guide

## Local Setup

```bash
git clone https://github.com/digitalocean-labs/do-app-platform-skills.git
cd do-app-platform-skills
make install
```

## Core Commands

Use [Makefile](../Makefile) targets where possible:

- `make test`
- `make test-cov`
- `make test-security`
- `make test-validation`
- `make ci`

## Typical Development Loop

1. Create/update skill content or scripts.
2. Run focused tests (for changed area).
3. Run validation gates (`validate_skills.py`, relevant pytest suites).
4. Run broader suite before opening PR.
5. Update docs/changelog with behavior changes.

## Modifying Skills Safely

- Keep skill-specific references close to the owning skill.
- Move shared logic/config to `shared/`.
- Preserve existing behavior unless intentionally versioned.
- Add tests for any changed script behavior.

## Script Development Guidance

- Use explicit error handling and clear operator-facing output.
- Prefer safe SQL handling patterns (parameterization and identifier-safe composition where required).
- Keep external calls mockable in tests.
- Avoid hidden side effects in helper scripts.

## Pull Request Expectations

A high-quality PR should include:

- Problem statement and scope
- Implementation summary
- Test evidence
- Security considerations (if applicable)
- Documentation updates

For contribution mechanics, see [CONTRIBUTING](../CONTRIBUTING.md).
