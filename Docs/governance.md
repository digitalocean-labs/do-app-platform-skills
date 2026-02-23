# Governance and Decision Process

## Governance Goals

- Keep technical quality and security bar high.
- Make decisions traceable and reversible.
- Preserve contributor velocity without sacrificing reliability.

## Decision Model

### Lightweight Decisions

Use pull request discussion for:

- small documentation fixes
- non-breaking test additions
- implementation refinements without contract impact

### Formal Decisions

Require issue + maintainer sign-off for:

- breaking changes
- deprecation/sunset actions
- major workflow or routing changes
- security-policy modifications

## Roles

- **Maintainers**: approve strategic and release-impacting changes.
- **Contributors**: propose changes with tests/docs.
- **Reviewers**: validate correctness, security, and scope control.

## RFC/Proposal Template (Recommended)

For major changes, include:

1. Problem statement
2. Proposed solution
3. Alternatives considered
4. Migration plan
5. Risk analysis
6. Validation plan

## Merge Standards

- Tests relevant to change scope must pass.
- Docs/changelog must reflect behavior changes.
- Security-sensitive changes require explicit reviewer attention.

## Conflict Resolution

When priorities conflict:

1. Favor security and correctness.
2. Favor compatibility for existing users.
3. Favor minimal safe change over broad rewrites.
