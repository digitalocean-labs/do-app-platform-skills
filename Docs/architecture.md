# Architecture

## System Type

This repository is a **knowledge architecture** for AI-assisted operations, not a deployable service.

Key components:

- **Root Router**: [SKILL.md](../SKILL.md) dispatches tasks to specialized skills.
- **Skill Modules**: `skills/<name>/` directories contain focused guidance and assets.
- **Shared Data Plane**: `shared/` contains reusable policy/config/reference data.
- **Validation + Tests**: `scripts/` and `tests/` enforce quality and safety.

## Repository Topology

```text
.
├── SKILL.md                     # Router
├── skills/                      # Specialized skills
├── shared/                      # Shared references and schema
├── scripts/                     # Utility + validation scripts
├── tests/                       # Test suites (unit/integration/security/etc.)
├── architecture/                # Workflow architecture notes
└── Docs/                        # Maintainer and OSS documentation
```

## Skill Module Contract

Each skill typically follows:

```text
skills/<skill>/
├── README.md
├── SKILL.md
├── reference/
├── scripts/      # optional
└── templates/    # optional
```

Design intent:

- `SKILL.md`: concise routing and execution behavior.
- `reference/`: deep details loaded as needed.
- `scripts/` + `templates/`: executable and reusable artifacts.

## Runtime Interaction Model

1. User asks for an App Platform outcome.
2. Router skill resolves workflow path.
3. Relevant sub-skill(s) provide policy + implementation patterns.
4. Scripts/templates produce concrete artifacts.
5. Tests/validation ensure correctness and security posture.

## Workflow Chaining Model

The system supports both:

- **Single-skill execution** (for isolated tasks like PostgreSQL setup), and
- **Multi-skill chaining** (for full lifecycle flows: design → plan → deploy → troubleshoot).

See [architecture/AGENT-WORKFLOWS.md](../architecture/AGENT-WORKFLOWS.md) for detailed orchestration patterns.

## Quality and Safety Gates

- Skill schema validation via [scripts/validate_skills.py](../scripts/validate_skills.py) and [shared/skill-schema.json](../shared/skill-schema.json).
- Pytest-based validation with markers and focused suites configured in [pytest.ini](../pytest.ini).
- Security-focused tests under `tests/test_security/` and relevant domain suites (for example, SQL-safety coverage in postgres tests).

## Architectural Constraints

- No credential persistence in docs/scripts output by default.
- No runtime service dependencies inside this repository.
- Changes must preserve existing skill contracts unless versioned accordingly.
