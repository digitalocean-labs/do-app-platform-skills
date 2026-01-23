---
name: app-platform-networking
version: 1.0.0
min_doctl_version: "1.82.0"
description: Configure domains, routing, CORS, VPC, static IPs, and inter-service communication for DigitalOcean App Platform. Use when setting up custom domains, subdomain routing, cross-origin API access, or secure database connectivity.
related_skills: [designer, postgres, managed-db-services]
deprecated: false
---

# App Platform Networking Skill

Configure domains, routing, CORS, VPC, static IPs, and inter-service communication.

## Quick Decision

```
What networking do you need?
├── Custom domain?
│   └── YES → See domains-dns.md
│
├── Multiple services on one domain?
│   ├── Different paths (/api, /app) → Path-based routing
│   └── Different subdomains (api.*, app.*) → Subdomain routing
│
├── Frontend calling API across origins?
│   └── YES → CORS configuration
│
├── Secure database connectivity?
│   └── YES → VPC + trusted sources
│
└── Need static outbound IP?
    └── YES → Dedicated egress
```

---

## When to Use

| Scenario | Need This Skill |
|----------|-----------------|
| Starter domain only | No |
| Custom domain | Yes |
| Multiple services, different paths | Yes |
| Multiple subdomains | Yes |
| Cross-subdomain API calls (CORS) | Yes |
| Secure database access via VPC | Yes |
| Firewall allowlisting (egress IP) | Yes |

---

## Quick Reference

| Feature | App Spec Field | Example |
|---------|----------------|---------|
| Custom domain | `domains[].domain` | `example.com` |
| Wildcard | `domains[].wildcard` | `true` |
| Path routing | `ingress.rules[].match.path.prefix` | `/api` |
| Subdomain routing | `ingress.rules[].match.authority.exact` | `api.example.com` |
| CORS | `ingress.rules[].cors` | See reference |
| VPC | `vpc.id` | UUID |
| Dedicated egress | `egress.type` | `DEDICATED_IP` |

---

## Path-Based Routing (Quick Start)

```yaml
ingress:
  rules:
    - component: { name: api }
      match: { path: { prefix: /api } }

    - component: { name: frontend }
      match: { path: { prefix: / } }
```

**Rule order matters:** Specific rules first.

**Full guide**: See [ingress-routing.md](reference/ingress-routing.md)

---

## Subdomain Routing (Quick Start)

```yaml
domains:
  - domain: example.com
    type: PRIMARY
    wildcard: true
    zone: example.com

ingress:
  rules:
    - component: { name: api }
      match:
        authority: { exact: api.example.com }
        path: { prefix: / }

    - component: { name: app }
      match:
        authority: { exact: app.example.com }
        path: { prefix: / }
```

**Full guide**: See [domains-dns.md](reference/domains-dns.md)

---

## CORS (Quick Start)

```yaml
ingress:
  rules:
    - component: { name: api }
      match: { path: { prefix: /api } }
      cors:
        allow_origins:
          - exact: https://app.example.com
        allow_methods: [GET, POST, PUT, DELETE, OPTIONS]
        allow_headers: [Content-Type, Authorization]
        allow_credentials: true
```

**Note:** With `allow_credentials: true`, use exact origins only (no regex).

**Full guide**: See [cors-configuration.md](reference/cors-configuration.md)

---

## VPC + Trusted Sources (Quick Start)

```yaml
vpc:
  id: your-vpc-uuid
```

**VPC CIDR whitelisting (recommended):**
```bash
doctl vpcs get $VPC_ID --format IPRange  # e.g., 10.126.0.0/20
doctl databases firewalls append $CLUSTER_ID --rule ip_addr:10.126.0.0/20
```

| Setup | Trusted Source Rule |
|-------|---------------------|
| Public only | `app:$APP_ID` |
| VPC enabled | `ip_addr:<vpc-cidr>` |

**Critical:** Bindable variables return PUBLIC hostnames even with VPC. Use private URLs:
```bash
doctl databases connection --private <cluster-id> --format URI
```

**Full guide**: See [vpc-trusted-sources.md](reference/vpc-trusted-sources.md)

---

## Reference Files

- **[domains-dns.md](reference/domains-dns.md)** — Domain types, DNS setup, wildcards, TLS, CAA
- **[ingress-routing.md](reference/ingress-routing.md)** — Path routing, rewrites, redirects, authority matching
- **[cors-configuration.md](reference/cors-configuration.md)** — CORS fields, patterns, credentials
- **[vpc-trusted-sources.md](reference/vpc-trusted-sources.md)** — VPC setup, trusted sources matrix, private URLs
- **[static-ips-egress.md](reference/static-ips-egress.md)** — Ingress IPs, dedicated egress, HTTP/2, internal ports
- **[complete-patterns.md](reference/complete-patterns.md)** — 5 complete architecture patterns

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Domain not resolving | Check DNS records, allow 72h propagation |
| SSL certificate error | Add CAA records for letsencrypt.org + pki.goog |
| CORS preflight fails | Add OPTIONS to allow_methods |
| VPC connection refused | Use VPC CIDR whitelisting, not app-based rules |
| Wrong component serves | Reorder rules (specific first) |

---

## Integration with Other Skills

- **→ designer**: Add domains/ingress to app spec
- **→ troubleshooting**: Debug DNS, CORS, VPC issues
- **→ postgres**: VPC connectivity for managed databases
- **→ deployment**: Deploy networking changes
