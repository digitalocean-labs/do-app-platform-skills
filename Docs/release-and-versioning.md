# Release and Versioning

## Versioning Strategy

This project follows semantic versioning guidance for skills and repository-level release notes.

- `MAJOR`: breaking behavior or contract changes
- `MINOR`: backward-compatible capability additions
- `PATCH`: fixes and non-breaking improvements

See [CHANGELOG](../CHANGELOG.md) and [CONTRIBUTING](../CONTRIBUTING.md).

## Release Checklist

1. Confirm all required suites pass.
2. Validate skill frontmatter/schema integrity.
3. Ensure changelog entries are complete and categorized.
4. Confirm docs updates for user-visible changes.
5. Ensure security-sensitive changes include regression coverage.

## Changelog Quality Bar

Each notable release entry should include:

- What changed
- Why it changed
- Whether migration/deprecation action is required

## Deprecation Process

- Mark deprecated in skill frontmatter.
- Add migration path and sunset date.
- Keep minimum deprecation window (as defined in contribution policy).
- Remove only in planned major release.

## Compatibility Guarantees

- Preserve documented behavior unless explicitly versioned.
- Document breaking changes with remediation guidance.
- Keep compatibility guidance synchronized with tool requirements.

## Post-Release Validation

After release:

- Re-run key suites on release branch/tag.
- Verify docs links and references resolve.
- Monitor issue tracker for regressions.
