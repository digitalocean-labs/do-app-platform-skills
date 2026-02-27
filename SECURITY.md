# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please report it responsibly.

- Do **not** open a public issue with exploit details.
- Contact maintainers through private channels first.
- Include reproduction steps, impact, and affected files where possible.

## What to Include

To speed triage, include:

- A clear description of the issue
- Impact assessment and likely blast radius
- Reproduction steps or proof of concept
- Suggested mitigation (if available)

## Response Expectations

Maintainers will aim to:

1. Acknowledge receipt promptly
2. Validate and triage severity
3. Provide remediation plan and timeline
4. Publish fix notes after patching

## Scope

Security-relevant areas in this repository include:

- credential handling patterns in scripts and docs
- SQL construction/execution safety in helper scripts
- generated artifacts that may be executed by users/agents
- CI/testing controls that prevent security regressions

For implementation guidance, see [Docs/security-model.md](Docs/security-model.md).
