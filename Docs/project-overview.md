# Project Overview

## Mission

DigitalOcean App Platform Skills provides high-signal, structured knowledge for AI assistants to generate and operate App Platform solutions safely and consistently.

This repository is intentionally **not** an application runtime. It is a skills-and-knowledge system with helper scripts, templates, and validation/tests.

## What This Repository Contains

- **Skill routers and references** for architecture, deployment, migration, networking, databases, AI services, and troubleshooting.
- **Operational helper scripts** for repeatable setup and validation tasks.
- **Shared reference assets** for opinionated defaults, schema validation, and platform data.
- **A comprehensive test suite** covering behavior, edge cases, and security-sensitive patterns.

## Scope

In scope:

- App Platform–specific decision support and artifact generation.
- Repeatable scripts/templates for common workflows.
- Security and credential-handling guidance for agent-assisted operations.

Out of scope:

- Running application business logic in production.
- Replacing official DigitalOcean product documentation.
- Storing user credentials/secrets in repository content.

## Product Principles

1. **Opinionated defaults over indecision**
2. **Artifacts over generic advice**
3. **Security-first handling of credentials and SQL**
4. **Composable workflow chaining across skills**
5. **Tested and versioned changes only**

## Primary Personas

- **Platform Engineer**: needs fast, safe deployment workflows.
- **Developer**: needs migration/setup guidance and templates.
- **Maintainer**: needs reliability, testability, and predictable release mechanics.

## Entry Points

- Start from the root [README](../README.md) for setup and usage.
- Use [Router Skill](../SKILL.md) to understand skill-routing behavior.
- Use [Architecture](architecture.md) to understand internals.
