# FAQ

## Is this a deployable app?

No. This repository is a skill and knowledge system with helper scripts/templates for App Platform operations.

## Where should new documentation go?

- Usage/onboarding basics: root [README](../README.md)
- Deep engineering/maintainer docs: `Docs/`
- Contribution process: [CONTRIBUTING](../CONTRIBUTING.md)

## How do I validate changes before opening a PR?

At minimum run:

```bash
python scripts/validate_skills.py
pytest -q tests/test_postgres
pytest
```

Then run additional focused suites for changed areas.

## Where are security expectations documented?

See [Security Model](security-model.md) and [shared/credential-patterns.md](../shared/credential-patterns.md).

## How are breaking changes handled?

Use semantic versioning and deprecation process documented in [CONTRIBUTING](../CONTRIBUTING.md) and [Release and Versioning](release-and-versioning.md).

## How do skills relate to each other?

The root [SKILL.md](../SKILL.md) defines routing and workflow chaining patterns. See [Architecture](architecture.md) for repository-level design.
