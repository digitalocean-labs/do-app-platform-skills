# Security Model

## Security Posture

This repository guides AI-assisted infrastructure operations. Security controls focus on preventing unsafe automation outcomes, especially around credentials and SQL execution.

## Threat Areas

1. **Credential leakage** in logs, generated files, or scripts.
2. **Unsafe SQL construction** when handling untrusted input.
3. **Configuration drift** from insecure defaults.
4. **Workflow misuse** due to ambiguous routing or undocumented constraints.

## Security Principles

- **Least exposure**: avoid printing secrets.
- **Safe defaults**: prefer managed secret stores and bindable variables.
- **Explicit trust boundaries**: treat user/agent-provided values as untrusted.
- **Regression prevention**: enforce with tests and reviews.

## Credential Handling Hierarchy

1. GitHub Secrets (preferred)
2. DigitalOcean bindable variables
3. Ephemeral values (generate-use-dispose)

Reference: [shared/credential-patterns.md](../shared/credential-patterns.md)

## SQL Safety Policy

For script execution paths:

- Do not build executable SQL via untrusted string interpolation.
- Use parameterized statements for values.
- Use identifier-safe composition where SQL identifiers are dynamic.

For generated SQL artifacts:

- Validate identifiers.
- Escape SQL literals correctly.
- Document that generated scripts require review before execution.

## Security Validation in Tests

- Use dedicated security tests (`tests/test_security/`).
- Add domain-specific regressions (for example, postgres SQL safety checks).
- Verify both safe behavior and absence of known anti-patterns.

## Vulnerability Handling

When a vulnerability is reported:

1. Reproduce and scope impact.
2. Fix root cause and add regression tests.
3. Validate affected suites.
4. Update changelog and relevant docs.
5. Communicate remediation clearly in PR notes.

## Responsible Disclosure

For newly discovered security issues, coordinate disclosure through maintainers before publishing exploit details in public issues.
