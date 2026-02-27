# Contributing Guidelines

Thank you for your interest in contributing!

Community contributions help improve the quality, safety, and usefulness of this repository for everyone building on DigitalOcean App Platform.

Please review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

1. Fork the repository.
2. Create a feature branch.
3. Add tests where appropriate.
4. Submit a pull request.

Recommended branch naming examples:

- `feat/designer-monorepo-improvements`
- `fix/migration-railway-detection`
- `docs/networking-cors-examples`

Recommended local workflow:

```bash
git clone https://github.com/<your-username>/do-app-platform-skills.git
cd do-app-platform-skills
git checkout -b feat/your-change

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python scripts/validate_skills.py
pytest -q
```

## Requirements

By submitting a contribution, you confirm that:

- You have the legal right to submit the code.
- The contribution is your original work or you have appropriate rights.
- The contribution will be licensed under the project’s MIT License.

Additional expectations for all submissions:

- Do not include secrets, private keys, access tokens, or customer data.
- Ensure generated artifacts, examples, and templates are safe for public distribution.
- Keep changes focused and minimal to the problem being solved.
- Update documentation when behavior, structure, or workflows change.

## Developer Certificate of Origin (DCO)

All commits must be signed off using:

Signed-off-by: Name <email>

This certifies that you have the right to submit the work.

### How to sign off commits

Use the `-s` flag on every commit:

```bash
git commit -s -m "feat: add migration validation edge case tests"
```

To verify sign-off lines in your recent commits:

```bash
git log --format=full --max-count=5
```

If a commit is missing sign-off, amend it:

```bash
git commit --amend -s
```

## Review Process

Maintainers will review submissions for quality, security, and alignment with project direction.
Submission does not guarantee acceptance.

### What maintainers check

- Functional correctness and repository consistency.
- Test coverage and regression risk.
- Security impact (credential handling, unsafe defaults, data exposure risk).
- Documentation quality and user-facing clarity.
- Alignment with project roadmap and architecture principles.

### Typical review outcomes

- **Accepted:** merged after required checks and approvals.
- **Changes requested:** updates needed before merge.
- **Declined:** out of scope, duplicates existing work, or does not meet project/legal/security standards.

## Code Style

Current linting and formatting-related rules are documented through project tooling:

- YAML lint target: [Makefile](Makefile#L56-L57)
- Lint dependency declaration (`yamllint`): [requirements-dev.txt](requirements-dev.txt#L10-L12)

Run lint checks before opening a pull request:

```bash
make lint
```

Project references for style and quality:

- [TESTING.md](TESTING.md)
- [SKILL.md](SKILL.md)
- [architecture/Docs/testing-and-quality.md](architecture/Docs/testing-and-quality.md)
- [architecture/Docs/developer-guide.md](architecture/Docs/developer-guide.md)

Practical style guidance:

- Keep skill content concise, actionable, and implementation-oriented.
- Preserve existing folder and naming conventions.
- Prefer explicit examples over abstract guidance.
- Keep scripts readable, deterministic, and safe by default.
- Include or update tests for any non-trivial behavior change.

## Reporting Issues

Please use GitHub Issues.
For security vulnerabilities, see [SECURITY.md](SECURITY.md).

When opening an issue, include:

- Problem summary and expected behavior.
- Reproduction steps and environment details.
- Relevant logs, stack traces, or command output.
- Proposed fix direction (if available).

### Additional guidance

For implementation and contribution flow patterns similar to DigitalOcean CLI, see:
https://github.com/digitalocean/doctl?tab=contributing-ov-file#issues
