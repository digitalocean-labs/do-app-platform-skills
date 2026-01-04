# Networking Skill

Configure domains, routing, CORS, VPC, static IPs, and inter-service communication for DigitalOcean App Platform.

## What This Skill Does

- Configures **custom domains** with DNS and TLS
- Sets up **path-based and subdomain routing** via ingress rules
- Configures **CORS** for cross-origin API access
- Enables **VPC networking** for secure database connectivity
- Manages **static egress IPs** for firewall allowlisting

## Quick Start

```yaml
# Path-based routing
ingress:
  rules:
    - component: { name: api }
      match: { path: { prefix: /api } }
    - component: { name: frontend }
      match: { path: { prefix: / } }
```

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| VPC connectivity | VPC CIDR whitelisting | More reliable than app-based rules |
| CORS credentials | Exact origins only | Required when `allow_credentials: true` |
| TLS certificates | Auto-provisioned | Let's Encrypt + Google Trust |
| Ingress order | Specific rules first | Prevents catch-all conflicts |

## Files

- `SKILL.md` — Complete skill documentation with quick starts
- `reference/domains-dns.md` — Domain types, DNS setup, wildcards, TLS
- `reference/ingress-routing.md` — Path routing, rewrites, redirects
- `reference/cors-configuration.md` — CORS fields, patterns, credentials
- `reference/vpc-trusted-sources.md` — VPC setup, trusted sources matrix
- `reference/static-ips-egress.md` — Ingress IPs, dedicated egress
- `reference/complete-patterns.md` — 5 complete architecture patterns

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | designer | Add domains/ingress to app spec |
| → | troubleshooting | Debug DNS, CORS, VPC issues |
| → | postgres | VPC connectivity for databases |
| → | deployment | Deploy networking changes |

## Related Skills

- **designer** — Include networking in app architecture
- **postgres** — Database VPC configuration
- **troubleshooting** — Debug connectivity issues
