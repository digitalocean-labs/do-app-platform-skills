# Skills and Content Model

## Why a Content Model?

A consistent content model allows agents and contributors to reason reliably across skills without relearning structure every time.

## Skill Definition Requirements

Each `SKILL.md` is expected to include validated frontmatter (see [shared/skill-schema.json](../shared/skill-schema.json)).

Core fields include:

- `name`
- `version`
- `min_doctl_version`
- `description`
- `related_skills`
- `deprecated`

Validate with:

```bash
python scripts/validate_skills.py
```

## Layered Content Strategy

- **Router layer**: fast routing and scope boundaries.
- **Reference layer**: detailed procedures and edge cases.
- **Artifact layer**: scripts/templates that produce output.

This separation keeps token usage efficient and limits context bloat.

## Shared Knowledge Reuse

Use `shared/` for cross-cutting references such as:

- app spec schema/patterns
- regions and instance sizes
- opinionated defaults
- credential and error patterns

Do not duplicate shared constants in multiple skills.

## Quality Heuristics for Skill Content

- Keep `SKILL.md` concise and actionable.
- Prefer examples that map to real App Platform constraints.
- Include explicit “use when” triggers and non-goals.
- Avoid embedding secrets or non-expiring credentials.

## Backward Compatibility in Content

- If behavior changes, update skill version and changelog.
- For deprecations, include migration guidance and sunset window.
- Breaking changes require explicit communication and version policy alignment.
