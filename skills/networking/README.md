# Networking Skill

Configure domains, routing, CORS, VPC, and inter-service communication for DigitalOcean App Platform applications.

## What This Skill Does

- Configure custom domains with wildcards and subdomains
- Set up ingress routing (path-based and subdomain-based)
- Configure CORS for cross-origin API access
- Enable VPC for secure internal communication
- Configure static IP addresses (ingress and egress)
- Set up edge settings (cache, DDoS protection)
- Enable HTTP/2 for gRPC services

## When to Use This Skill

| Scenario | Use This Skill |
|----------|----------------|
| Single service + starter domain | No |
| Custom domain setup | Yes |
| Multiple services on different paths | Yes |
| Multiple services on different subdomains | Yes |
| Cross-subdomain API calls | Yes |
| Connecting to managed databases via VPC | Yes |
| Firewall allowlisting (dedicated egress IP) | Yes |
| gRPC or HTTP/2 services | Yes |

## Quick Start

**Simple custom domain:**
```yaml
domains:
  - domain: example.com
    type: PRIMARY
```

**Subdomain routing (API + App):**
```yaml
domains:
  - domain: example.com
    wildcard: true
    zone: example.com

ingress:
  rules:
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
    - component:
        name: frontend
      match:
        authority:
          exact: app.example.com
```

## Files

- `SKILL.md` — Complete documentation with all patterns, CORS configuration, VPC setup, and reference examples

## Related Skills

- **designer** — Generates base app specs (basic routing included)
- **troubleshooting** — Debug networking issues (DNS, CORS, VPC connectivity)
- **postgres** — Database connection via VPC
