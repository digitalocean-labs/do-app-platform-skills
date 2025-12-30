# App Platform Networking Skill

Configure domains, routing, CORS, VPC, static IPs, and inter-service communication for DigitalOcean App Platform.

---

## Overview

### When to Use This Skill

| Scenario | Need This Skill |
|----------|-----------------|
| Single service + starter domain only | No |
| Custom domain setup | Yes |
| Multiple services, different paths (`/api`, `/app`) | Yes |
| Multiple services, different subdomains (`api.`, `app.`) | Yes |
| Cross-subdomain API calls (CORS) | Yes |
| Secure database access via VPC | Yes |
| Firewall allowlisting (dedicated egress IP) | Yes |
| gRPC or HTTP/2 services | Yes |
| DDoS protection | Yes |

### Quick Reference

| Feature | App Spec Field | Example |
|---------|----------------|---------|
| Custom domain | `domains[].domain` | `example.com` |
| Wildcard domain | `domains[].wildcard` | `true` |
| DO-managed DNS | `domains[].zone` | `example.com` |
| TLS version | `domains[].minimum_tls_version` | `"1.3"` |
| Path routing | `ingress.rules[].match.path.prefix` | `/api` |
| Subdomain routing | `ingress.rules[].match.authority.exact` | `api.example.com` |
| HTTP redirect | `ingress.rules[].redirect` | See examples |
| CORS | `ingress.rules[].cors` | See examples |
| VPC | `vpc.id` | UUID |
| Dedicated egress | `egress.type` | `DEDICATED_IP` |
| HTTP/2 | `services[].protocol` | `HTTP2` |
| Internal ports | `services[].internal_ports` | `[9090]` |
| Edge cache | `disable_edge_cache` | `true` |
| DDoS protection | `enhanced_threat_control_enabled` | `true` |

---

## Domains

### Domain Types

| Type | Purpose |
|------|---------|
| `PRIMARY` | Main domain for the app (one per app) |
| `ALIAS` | Additional domains pointing to the same app |

```yaml
domains:
  - domain: example.com
    type: PRIMARY
  - domain: www.example.com
    type: ALIAS
  - domain: app.example.com
    type: ALIAS
```

### Starter Domain vs Custom Domain

Every App Platform app gets a free starter domain: `your-app-name.ondigitalocean.app`

| Aspect | Starter Domain | Custom Domain |
|--------|----------------|---------------|
| Cost | Free | Free (domain registration separate) |
| SSL | Automatic | Automatic |
| Edge features | No | Yes |
| Subdomain routing | No | Yes |
| Wildcard | No | Yes |

### DNS Setup Options

**Option 1: DigitalOcean-Managed DNS (Recommended)**

Use the `zone` field to let DigitalOcean manage DNS:

```yaml
domains:
  - domain: example.com
    type: PRIMARY
    zone: example.com  # DO manages DNS
```

Point your registrar's nameservers to:
- `ns1.digitalocean.com`
- `ns2.digitalocean.com`
- `ns3.digitalocean.com`

**Option 2: CNAME Pointer (Self-Managed DNS)**

Add a CNAME record pointing to your app's starter domain:

```
CNAME  app.example.com  →  your-app.ondigitalocean.app
```

For apex domains (example.com without subdomain), use A records pointing to App Platform's ingress IPs:
- `162.159.140.98` (IPv4)
- `172.66.0.96` (IPv4)
- `2606:4700:7::60` (IPv6)
- `2a06:98c1:58::60` (IPv6)

### Wildcard Domains

Enable wildcard to route any subdomain:

```yaml
domains:
  - domain: example.com
    type: PRIMARY
    wildcard: true
    zone: example.com
```

**Wildcard Validation:**
- Requires TXT record validation
- DigitalOcean provides TXT name and value
- Add to your DNS provider
- Re-validate every 30 days (notification sent)

**Wildcard Limitations:**
- Not supported for TLDs listed on DigiCert reference page
- Must add root domain first, then wildcard

### TLS/SSL Configuration

```yaml
domains:
  - domain: example.com
    type: PRIMARY
    minimum_tls_version: "1.3"  # Options: "1.2" or "1.3"
```

### CAA Records

If your domain uses CAA records, add both CAs:

```
CAA 0 issue "letsencrypt.org"
CAA 0 issue "pki.goog"
```

App Platform uses LetsEncrypt and Google Trust as Certificate Authorities.

---

## Ingress and Routing

App Platform uses `ingress.rules` for all routing configuration. The deprecated `routes` field should be migrated to `ingress`.

### Path-Based Routing

Route requests to different components based on URL path:

```yaml
ingress:
  rules:
    # /api/* goes to api service
    - component:
        name: api
      match:
        path:
          prefix: /api

    # Everything else goes to frontend
    - component:
        name: frontend
      match:
        path:
          prefix: /
```

**Rule order matters:** More specific rules should come first.

### Path Rewriting

Strip or modify the path before forwarding to the component:

```yaml
ingress:
  rules:
    # /v1/api/* is rewritten to /api/* before forwarding
    - component:
        name: api
        rewrite: /api
      match:
        path:
          prefix: /v1/api
```

### preserve_path_prefix

Control whether the matched prefix is forwarded:

```yaml
# With preserve_path_prefix: true
# Request: /api/users/123
# Component receives: /api/users/123

# With preserve_path_prefix: false (or using rewrite)
# Request: /api/users/123
# Component receives: /users/123
```

### Authority-Based Routing (Subdomain Routing)

Route requests based on the hostname (subdomain):

```yaml
ingress:
  rules:
    # api.example.com → api service
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /

    # app.example.com → frontend service
    - component:
        name: frontend
      match:
        authority:
          exact: app.example.com
        path:
          prefix: /
```

### Regex Authority Matching

Match subdomains with patterns:

```yaml
ingress:
  rules:
    # Any tenant subdomain (tenant1.example.com, tenant2.example.com)
    - component:
        name: tenant-app
      match:
        authority:
          regex: ^[a-z0-9-]+\.example\.com$
        path:
          prefix: /
```

### Combined Authority + Path Routing

Route by both subdomain AND path:

```yaml
ingress:
  rules:
    # api.example.com/v1/* → legacy API
    - component:
        name: api-legacy
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /v1

    # api.example.com/v2/* → new API
    - component:
        name: api-v2
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /v2

    # api.example.com/* (catch-all) → latest API
    - component:
        name: api-v2
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /
```

### HTTP Redirects

Redirect requests to a different URL:

```yaml
ingress:
  rules:
    # Redirect /old-path to /new-path
    - redirect:
        uri: /new-path
        redirect_code: 301
      match:
        path:
          prefix: /old-path

    # Redirect to different domain
    - redirect:
        authority: newsite.com
        uri: /
        redirect_code: 302
      match:
        path:
          prefix: /legacy
```

**Redirect codes:**
| Code | Meaning | Use Case |
|------|---------|----------|
| 301 | Moved Permanently | SEO-friendly permanent redirect |
| 302 | Found (Temporary) | Default, temporary redirect |
| 307 | Temporary Redirect | Preserve HTTP method |
| 308 | Permanent Redirect | Preserve HTTP method |

### Starter Domain Redirect

Redirect the starter domain to your custom domain:

```yaml
ingress:
  rules:
    # Redirect starter domain to custom domain
    - redirect:
        authority: app.example.com
        redirect_code: 301
      match:
        authority:
          exact: ${STARTER_DOMAIN}
        path:
          prefix: /
```

The `${STARTER_DOMAIN}` placeholder matches your app's `*.ondigitalocean.app` domain.

### www to non-www Redirect

```yaml
ingress:
  rules:
    - redirect:
        authority: example.com
        redirect_code: 301
      match:
        authority:
          exact: www.example.com
        path:
          prefix: /
```

### Rewrites vs Redirects

| Aspect | Rewrite | Redirect |
|--------|---------|----------|
| URL in browser | Unchanged | Changes |
| HTTP status | 200 | 301/302/etc |
| Cross-domain | No | Yes |
| SEO | Single URL | Can split link equity |
| Use case | Internal path mapping | External URL changes |

---

## CORS Configuration

Cross-Origin Resource Sharing (CORS) controls which domains can make API requests to your services.

### Basic CORS Configuration

```yaml
ingress:
  rules:
    - component:
        name: api
      match:
        path:
          prefix: /api
      cors:
        allow_origins:
          - exact: https://example.com
        allow_methods:
          - GET
          - POST
        allow_headers:
          - Content-Type
        max_age: "1h"
```

### CORS Fields

| Field | Description | Example |
|-------|-------------|---------|
| `allow_origins` | Domains allowed to make requests | See below |
| `allow_methods` | HTTP methods allowed | `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS` |
| `allow_headers` | Request headers allowed | `Content-Type`, `Authorization` |
| `expose_headers` | Response headers exposed to scripts | `X-Request-ID` |
| `max_age` | Cache duration for preflight | `"1h"`, `"24h"` (max) |
| `allow_credentials` | Allow cookies/auth headers | `true` or `false` |

### allow_origins Patterns

**Exact match:**
```yaml
allow_origins:
  - exact: https://example.com
  - exact: https://app.example.com
```

**Regex match:**
```yaml
allow_origins:
  - regex: ^https://.*\.example\.com$
```

**Combined:**
```yaml
allow_origins:
  - exact: https://example.com
  - exact: https://app.example.com
  - regex: ^https://[a-z0-9-]+\.example\.com$
```

### Cross-Subdomain CORS

When services on different subdomains need to communicate:

```yaml
ingress:
  rules:
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /
      cors:
        allow_origins:
          - exact: https://app.example.com
          - exact: https://admin.example.com
          - exact: https://ai.example.com
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        allow_headers:
          - Content-Type
          - Authorization
          - X-Request-ID
        expose_headers:
          - X-Request-ID
        max_age: "1h"
        allow_credentials: true
```

### CORS with Credentials

When using `allow_credentials: true`:
- Cannot use wildcard (`*`) in `allow_origins`
- Must specify exact origins
- Cookies and auth headers will be sent

```yaml
cors:
  allow_origins:
    - exact: https://app.example.com  # Must be exact, not regex
  allow_credentials: true
```

### Preflight Requests

Browsers send OPTIONS preflight requests for:
- Non-simple methods (PUT, DELETE, PATCH)
- Custom headers (Authorization, X-Custom-Header)
- Content-Type other than form-urlencoded, multipart/form-data, text/plain

Always include `OPTIONS` in `allow_methods` if using these features:

```yaml
cors:
  allow_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS  # Required for preflight
```

---

## VPC Configuration

Virtual Private Cloud (VPC) enables secure private network communication between App Platform apps and other DigitalOcean resources.

### What VPC Enables

- Private network access to managed databases
- Communication with Droplets over private IPs
- Communication with Kubernetes clusters
- Cross-datacenter communication via VPC peering

### Regional Datacenter Mapping

Apps connect to VPCs in their region's specific datacenter:

| App Region | VPC Datacenter |
|------------|----------------|
| ams | ams3 |
| blr | blr1 |
| fra | fra1 |
| lon | lon1 |
| nyc | nyc1 |
| sfo | sfo3 |
| sgp | sgp1 |
| syd | syd1 |
| tor | tor1 |

### Enabling VPC

**Step 1: Get VPC UUID**

```bash
doctl vpcs list
```

Or from Control Panel URL: `https://cloud.digitalocean.com/networking/vpc/{uuid}/...`

**Step 2: Add to App Spec**

```yaml
name: my-app
region: nyc

vpc:
  id: c22d8f48-4bc4-49f5-8ca0-58e7164427ac

services:
  - name: api
    # ... service config
```

### Connecting to Managed Databases with VPC + Trusted Sources

**Recommended approach:** Use VPC + IP-based trusted sources for secure database access.

**Step 1: Enable VPC on your app** (see above)

**Step 2: Deploy and get the VPC egress private IP**

After deploying with VPC enabled, find your app's VPC egress IP:

```bash
# Via API/doctl - look for egress IP in app info
doctl apps get <app_id> -o json | jq '.[] | .dedicated_ips'

# Or from the App Platform console:
# Apps → Your App → Settings → scroll to "Network" section
# Look for "VPC Egress IP" or "Private IP"
```

**For AI Assistants** — Use the `do-app-sandbox` SDK:

```python
from do_app_sandbox import Sandbox

app = Sandbox.get_from_id(app_id="your-app-id", component="your-component")
result = app.exec("ip addr show | grep 'inet 10\\.'")
print(result.stdout)  # Look for 10.x.x.x private IP
```

**For Humans** — Use the interactive console:

```bash
doctl apps console <app_id> <component>
ip addr show | grep "inet 10\."
```

**Step 3: Add the private IP to database trusted sources**

```bash
# Get your database cluster ID
CLUSTER_ID=$(doctl databases list --format ID,Name --no-header | grep my-db | awk '{print $1}')

# Add the VPC egress private IP (NOT the app ID)
doctl databases firewalls append $CLUSTER_ID --rule ip_addr:<your-vpc-egress-ip>

# Verify
doctl databases firewalls list $CLUSTER_ID
```

> **Important:** You cannot simply select "App Platform" in trusted sources when using VPC. You must find the app's VPC egress private IP and add that specific IP address.

**Step 4: Use private connection string**

```yaml
databases:
  - name: db
    engine: PG
    production: true

services:
  - name: api
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}  # Uses internal hostname when VPC enabled
```

### Trusted Sources Compatibility

| Database | Trusted Sources | Notes |
|----------|-----------------|-------|
| PostgreSQL | Supported | Use VPC egress IP |
| MySQL | Supported | Use VPC egress IP |
| MongoDB | Supported | Use VPC egress IP |
| Valkey/Redis | Supported | Use VPC egress IP |
| **Kafka** | **NOT SUPPORTED** | Must disable trusted sources entirely |
| OpenSearch | Partial | Works for queries, **NOT for log forwarding** |

> **Kafka Warning:** App Platform cannot connect to Kafka clusters with trusted sources enabled. You must disable trusted sources on the Kafka cluster before integrating.

> **OpenSearch Warning:** If you want App Platform to forward logs to OpenSearch, you must disable trusted sources. Regular database queries work fine with trusted sources.

### VPC Limitations

- **Functions not supported:** VPC does not work with Function components
- **Single datacenter:** Direct connections limited to one datacenter per region
- **Trusted sources:** Requires IP-based whitelist (not app ID) for VPC connections
- **IP changes on redeploy:** VPC egress IP may change on major redeployments; monitor and update trusted sources if needed

### Verifying VPC Connectivity

From App Platform console terminal:

```bash
# Check if app is in VPC
ip addr show

# Test connectivity to a Droplet
curl http://<droplet-private-ip>:<port>

# Test database connectivity
nc -zv <db-private-hostname> <port>
```

---

## Static IP Addresses

### Ingress IPs (Free)

App Platform provides shared public IPs for incoming traffic:

| Type | Address |
|------|---------|
| IPv4 | `162.159.140.98` |
| IPv4 | `172.66.0.96` |
| IPv6 | `2606:4700:7::60` |
| IPv6 | `2a06:98c1:58::60` |

Use these for DNS A/AAAA records when self-managing DNS.

### Dedicated Egress IPs (Paid Feature)

Route **outbound** traffic through dedicated, non-shared IP addresses.

**Use cases:**
- Firewall allowlisting on external APIs
- IP-based authentication with third-party services
- Audit and compliance requirements

**Enable in app spec:**

```yaml
name: my-app
region: nyc

egress:
  type: DEDICATED_IP

services:
  - name: api
    # ... service config
```

**Enable via Control Panel:**
1. Apps → Your App → Settings
2. Find "Dedicated Egress IP Addresses"
3. Click Edit → Add Dedicated Egress IP
4. Two IPs are assigned; app redeploys

### Dedicated Egress Limitations

| Limitation | Details |
|------------|---------|
| App-level only | Applies to all components except functions |
| Functions excluded | Function components cannot use dedicated egress |
| Log forwarding | Uses separate routing, not dedicated egress |
| No IPv6 | Only IPv4 dedicated egress available |
| Permanent release | IPs are permanently released when disabled; cannot be recovered |

---

## Edge Settings

Edge settings configure CDN and security features at the edge layer. **Requires custom domain** (not available on starter domains).

### Available Settings

| Setting | App Spec Field | Default | Effect |
|---------|----------------|---------|--------|
| CDN Cache | `disable_edge_cache` | false (enabled) | Cache static responses at edge |
| Email Obfuscation | `disable_email_obfuscation` | false (enabled) | Protect emails from scrapers |
| DDoS Protection | `enhanced_threat_control_enabled` | false | Layer 7 DDoS protection |

### Configuration

```yaml
name: my-app
region: nyc

# Disable CDN caching (for dynamic content)
disable_edge_cache: true

# Disable email obfuscation
disable_email_obfuscation: true

# Enable enhanced DDoS protection
enhanced_threat_control_enabled: true

domains:
  - domain: example.com
    type: PRIMARY
```

### Edge Settings Notes

- Apply to **all custom domains** on the app
- Changes propagate within ~30 seconds
- Not available on starter domains
- Boolean values apply app-wide

---

## HTTP/2 and Protocols

### Enabling HTTP/2

Enable HTTP/2 for gRPC services or improved performance:

```yaml
services:
  - name: grpc-service
    git:
      repo_clone_url: https://github.com/org/grpc.git
      branch: main
    http_port: 50051
    protocol: HTTP2
```

### When to Use HTTP/2

| Use Case | Protocol |
|----------|----------|
| gRPC services | HTTP2 (required) |
| SSE (Server-Sent Events) | HTTP2 (recommended) |
| Standard web apps | HTTP/1.1 (default) |
| REST APIs | HTTP/1.1 (default) |

### HTTP/2 Notes

- Traffic arrives at container as HTTP/2 cleartext (h2c)
- Your app must support HTTP/2
- If not configured, App Platform downgrades to HTTP/1.1
- SSE with HTTP/1.1 may hit connection limits

---

## Internal Service Communication

### Service-to-Service URLs

Components can communicate internally using environment variable placeholders:

| Placeholder | Resolves To |
|-------------|-------------|
| `${service-name.PRIVATE_URL}` | Internal URL (private network) |
| `${service-name.PUBLIC_URL}` | External URL (public internet) |
| `${APP_URL}` | App's default URL |

```yaml
services:
  - name: api
    envs:
      - key: AUTH_SERVICE_URL
        scope: RUN_TIME
        value: ${auth.PRIVATE_URL}
      - key: PUBLIC_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}

  - name: auth
    # ... auth service config
```

### Internal DNS

Services can reach each other using the service name as hostname:

```
http://service-name
http://service-name:port
```

Example:
- Service named `web` is reachable at `http://web`
- With internal port 9090: `http://web:9090`

### Internal Ports

Configure additional ports for internal-only traffic:

```yaml
services:
  - name: api
    http_port: 8080        # Public HTTP port
    internal_ports:
      - 9090               # Internal gRPC port
      - 9091               # Internal metrics port
```

Other services can reach:
- `http://api:8080` (public port, also accessible internally)
- `http://api:9090` (internal only)
- `http://api:9091` (internal only)

### Worker and Job Communication

Workers and jobs can send **outbound** requests but cannot receive inbound requests:

```yaml
workers:
  - name: background-worker
    envs:
      - key: API_URL
        scope: RUN_TIME
        value: ${api.PRIVATE_URL}  # Worker calls API internally
```

### When to Use PRIVATE_URL vs PUBLIC_URL

| Scenario | Use |
|----------|-----|
| Backend service calling another backend | `PRIVATE_URL` |
| Worker processing jobs | `PRIVATE_URL` |
| Frontend build-time API URL | `PUBLIC_URL` |
| External webhook callbacks | `PUBLIC_URL` |
| Database connection | `PRIVATE_URL` (with VPC) |

---

## Complete Patterns

### Pattern 1: Single Service + Custom Domain

Simple app with custom domain:

```yaml
name: simple-app
region: nyc

domains:
  - domain: example.com
    type: PRIMARY

services:
  - name: web
    git:
      repo_clone_url: https://github.com/org/app.git
      branch: main
    http_port: 3000

ingress:
  rules:
    # Redirect starter domain to custom domain
    - redirect:
        authority: example.com
        redirect_code: 301
      match:
        authority:
          exact: ${STARTER_DOMAIN}
        path:
          prefix: /
```

### Pattern 2: API + Frontend (Path-Based Routing)

Separate API and frontend on different paths:

```yaml
name: fullstack-app
region: nyc

domains:
  - domain: example.com
    type: PRIMARY

services:
  - name: api
    git:
      repo_clone_url: https://github.com/org/api.git
      branch: main
    http_port: 8080

static_sites:
  - name: frontend
    git:
      repo_clone_url: https://github.com/org/frontend.git
      branch: main
    build_command: npm run build
    output_dir: dist

ingress:
  rules:
    - component:
        name: api
      match:
        path:
          prefix: /api
      cors:
        allow_origins:
          - exact: https://example.com
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        allow_headers:
          - Content-Type
          - Authorization
        max_age: "1h"

    - component:
        name: frontend
      match:
        path:
          prefix: /
```

### Pattern 3: Microservices (Subdomain-Based Routing)

Multiple services on different subdomains:

```yaml
name: microservices-app
region: nyc

domains:
  - domain: example.com
    type: PRIMARY
    wildcard: true
    zone: example.com

services:
  - name: api
    git:
      repo_clone_url: https://github.com/org/api.git
      branch: main
    http_port: 8080

  - name: app
    git:
      repo_clone_url: https://github.com/org/app.git
      branch: main
    http_port: 3000

  - name: admin
    git:
      repo_clone_url: https://github.com/org/admin.git
      branch: main
    http_port: 3000

ingress:
  rules:
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /
      cors:
        allow_origins:
          - exact: https://app.example.com
          - exact: https://admin.example.com
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        allow_headers:
          - Content-Type
          - Authorization
        max_age: "1h"
        allow_credentials: true

    - component:
        name: app
      match:
        authority:
          exact: app.example.com
        path:
          prefix: /

    - component:
        name: admin
      match:
        authority:
          exact: admin.example.com
        path:
          prefix: /

    # Root domain redirect to app
    - redirect:
        authority: app.example.com
        redirect_code: 301
      match:
        authority:
          exact: example.com
        path:
          prefix: /

    # www redirect
    - redirect:
        authority: app.example.com
        redirect_code: 301
      match:
        authority:
          exact: www.example.com
        path:
          prefix: /
```

### Pattern 4: Multi-Tenant SaaS (Wildcard Subdomains)

Tenant-specific subdomains:

```yaml
name: saas-app
region: nyc

domains:
  - domain: example.com
    type: PRIMARY
    wildcard: true
    zone: example.com

services:
  - name: tenant-app
    git:
      repo_clone_url: https://github.com/org/tenant-app.git
      branch: main
    http_port: 3000
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

databases:
  - name: db
    engine: PG
    production: true

ingress:
  rules:
    # Marketing site on root domain
    - component:
        name: marketing
      match:
        authority:
          exact: example.com
        path:
          prefix: /

    # API on api subdomain
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /

    # Any other subdomain goes to tenant app
    - component:
        name: tenant-app
      match:
        authority:
          regex: ^[a-z0-9-]+\.example\.com$
        path:
          prefix: /
```

### Pattern 5: Full 7-Service Enterprise Architecture

Complete enterprise setup with:
- Multiple subdomains
- Internal service communication
- VPC for database access
- Dedicated egress IPs
- HTTP/2 for gRPC
- Cross-subdomain CORS

```yaml
name: enterprise-app
region: nyc

# Wildcard domain for multi-subdomain routing
domains:
  - domain: example.com
    type: PRIMARY
    wildcard: true
    zone: example.com
    minimum_tls_version: "1.3"

# VPC for secure internal communication
vpc:
  id: your-vpc-uuid

# Dedicated egress for firewall allowlisting
egress:
  type: DEDICATED_IP

# Enhanced DDoS protection
enhanced_threat_control_enabled: true

services:
  # 1. Main API service
  - name: api
    git:
      repo_clone_url: https://github.com/org/api.git
      branch: main
    http_port: 8080
    internal_ports:
      - 9090  # Internal gRPC
    instance_size_slug: apps-s-1vcpu-1gb
    instance_count: 2
    envs:
      - key: AUTH_SERVICE_URL
        scope: RUN_TIME
        value: ${auth.PRIVATE_URL}
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: GRPC_SERVICE_URL
        scope: RUN_TIME
        value: http://grpc-service:50051

  # 2. Auth service (internal only)
  - name: auth
    git:
      repo_clone_url: https://github.com/org/auth.git
      branch: main
    http_port: 8080
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: JWT_SECRET
        scope: RUN_TIME
        type: SECRET
        value: CHANGE_ME

  # 3. AI Dashboard service
  - name: ai-dashboard
    git:
      repo_clone_url: https://github.com/org/ai-dashboard.git
      branch: main
    http_port: 3000
    envs:
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: https://api.example.com

  # 4. Main Dashboard
  - name: dashboard
    git:
      repo_clone_url: https://github.com/org/dashboard.git
      branch: main
    http_port: 3000
    envs:
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: https://api.example.com
      - key: NEXT_PUBLIC_AI_DASHBOARD_URL
        scope: BUILD_TIME
        value: https://ai.example.com

  # 5. Marketing site
  - name: marketing
    git:
      repo_clone_url: https://github.com/org/marketing.git
      branch: main
    http_port: 3000

  # 6. Admin panel
  - name: admin
    git:
      repo_clone_url: https://github.com/org/admin.git
      branch: main
    http_port: 3000
    envs:
      - key: NEXT_PUBLIC_API_URL
        scope: BUILD_TIME
        value: https://api.example.com

  # 7. gRPC service (HTTP/2)
  - name: grpc-service
    git:
      repo_clone_url: https://github.com/org/grpc-service.git
      branch: main
    http_port: 50051
    protocol: HTTP2
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

workers:
  # Background job processor
  - name: worker
    git:
      repo_clone_url: https://github.com/org/worker.git
      branch: main
    instance_size_slug: apps-s-1vcpu-0.5gb
    envs:
      - key: API_INTERNAL_URL
        scope: RUN_TIME
        value: ${api.PRIVATE_URL}
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

jobs:
  # Database migrations
  - name: migrate
    git:
      repo_clone_url: https://github.com/org/api.git
      branch: main
    kind: PRE_DEPLOY
    run_command: npm run migrate
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}

databases:
  - name: db
    engine: PG
    production: true
    cluster_name: enterprise-db

ingress:
  rules:
    # API subdomain with CORS for all app subdomains
    - component:
        name: api
      match:
        authority:
          exact: api.example.com
        path:
          prefix: /
      cors:
        allow_origins:
          - exact: https://app.example.com
          - exact: https://ai.example.com
          - exact: https://admin.example.com
          - regex: ^https://.*\.example\.com$
        allow_methods:
          - GET
          - POST
          - PUT
          - DELETE
          - PATCH
          - OPTIONS
        allow_headers:
          - Content-Type
          - Authorization
          - X-Request-ID
        expose_headers:
          - X-Request-ID
          - X-RateLimit-Remaining
        max_age: "1h"
        allow_credentials: true

    # AI Dashboard subdomain
    - component:
        name: ai-dashboard
      match:
        authority:
          exact: ai.example.com
        path:
          prefix: /

    # Main app subdomain
    - component:
        name: dashboard
      match:
        authority:
          exact: app.example.com
        path:
          prefix: /

    # Admin subdomain
    - component:
        name: admin
      match:
        authority:
          exact: admin.example.com
        path:
          prefix: /

    # Marketing on root domain
    - component:
        name: marketing
      match:
        authority:
          exact: example.com
        path:
          prefix: /

    # www redirect to root domain
    - redirect:
        authority: example.com
        redirect_code: 301
      match:
        authority:
          exact: www.example.com
        path:
          prefix: /

    # Starter domain redirect to main app
    - redirect:
        authority: app.example.com
        redirect_code: 301
      match:
        authority:
          exact: ${STARTER_DOMAIN}
        path:
          prefix: /

alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: DOMAIN_FAILED
```

---

## Validation

Always validate your app spec before deployment:

```bash
doctl apps spec validate .do/app.yaml
```

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `routes is deprecated` | Using old routing | Switch to `ingress.rules` |
| `invalid domain` | Domain format wrong | Check domain syntax |
| `wildcard requires zone` | Wildcard without DO DNS | Add `zone` field or use CNAME |
| `ingress rule conflict` | Overlapping rules | Reorder rules, specific first |
| `CORS allow_credentials with regex` | Regex origins with credentials | Use exact origins only |

---

## References

- [Manage Domains](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains/)
- [Configure CORS](https://docs.digitalocean.com/products/app-platform/how-to/configure-cors-policies/)
- [URL Rewrites/Redirects](https://docs.digitalocean.com/products/app-platform/how-to/rewrite-redirect-urls/)
- [Internal Routing](https://docs.digitalocean.com/products/app-platform/how-to/internal-routing/)
- [Enable VPC](https://docs.digitalocean.com/products/app-platform/how-to/enable-vpc/)
- [Static IP Addresses](https://docs.digitalocean.com/products/app-platform/how-to/add-ip-address/)
- [Edge Settings](https://docs.digitalocean.com/products/app-platform/how-to/configure-edge-settings/)
- [Configure HTTP/2](https://docs.digitalocean.com/products/app-platform/how-to/configure-http2/)
