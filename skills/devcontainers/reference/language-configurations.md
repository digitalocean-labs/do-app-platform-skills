# Language Configurations

Hot reload and development server configurations for different programming languages in devcontainers.

---

## Enabling Languages in devcontainer.json

```json
"features": {
  // Always enabled (needed for tooling)
  "ghcr.io/devcontainers/features/node:1": {},
  "ghcr.io/devcontainers/features/python:1": {},

  // Uncomment as needed
  // "ghcr.io/devcontainers/features/go:1": {},
  // "ghcr.io/devcontainers/features/rust:1": {},
  // "ghcr.io/devcontainers/features/ruby:1": {},
  // "ghcr.io/devcontainers/features/php:1": {},
}
```

---

## Node.js

### Using nodemon (JavaScript)

**package.json:**
```json
{
  "scripts": {
    "dev": "nodemon src/index.js"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}
```

**nodemon.json (optional):**
```json
{
  "watch": ["src"],
  "ext": "js,json",
  "ignore": ["node_modules"],
  "exec": "node src/index.js"
}
```

### Using tsx (TypeScript)

**package.json:**
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts"
  },
  "devDependencies": {
    "tsx": "^4.0.0"
  }
}
```

### Using Next.js

```bash
npm run dev
# or
next dev --turbo
```

### Using Vite

```bash
npm run dev
# Vite automatically enables HMR
```

---

## Python

### FastAPI with Uvicorn

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**pyproject.toml (with uv):**
```toml
[project.scripts]
dev = "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
```

### Flask

```bash
flask run --debug --host 0.0.0.0 --port 5000
```

**Alternative with python-dotenv:**
```bash
FLASK_DEBUG=1 flask run --host 0.0.0.0
```

### Django

```bash
python manage.py runserver 0.0.0.0:8000
```

**With django-extensions for auto-reload:**
```bash
python manage.py runserver_plus 0.0.0.0:8000
```

---

## Go

### Using Air (recommended)

Install air:
```bash
go install github.com/air-verse/air@latest
```

**.air.toml:**
```toml
root = "."
tmp_dir = "tmp"

[build]
cmd = "go build -o ./tmp/main ."
bin = "tmp/main"
include_ext = ["go", "tpl", "tmpl", "html"]
exclude_dir = ["tmp", "vendor", "node_modules"]
delay = 1000

[log]
time = false

[color]
main = "magenta"
watcher = "cyan"
build = "yellow"
runner = "green"

[misc]
clean_on_exit = true
```

Run:
```bash
air
```

### Using entr (alternative)

```bash
find . -name '*.go' | entr -r go run .
```

---

## Rust

### Using cargo-watch

Install:
```bash
cargo install cargo-watch
```

Run:
```bash
cargo watch -x run
```

With automatic restart on crash:
```bash
cargo watch -x 'run --release'
```

---

## Ruby

### Rails

```bash
rails server -b 0.0.0.0 -p 3000
```

With rerun for non-Rails apps:
```bash
gem install rerun
rerun 'ruby app.rb'
```

---

## PHP

### Laravel

```bash
php artisan serve --host=0.0.0.0 --port=8000
```

### Symfony

```bash
symfony server:start --no-tls
```

---

## Environment-Specific Configuration

### Detecting Local Development

```typescript
// TypeScript/JavaScript
const isDev = process.env.NODE_ENV !== 'production' ||
              process.env.DATABASE_URL?.includes('localhost') ||
              process.env.DATABASE_URL?.includes('postgres:');
```

```python
# Python
import os

is_dev = (
    os.environ.get('FLASK_ENV') == 'development' or
    os.environ.get('DEBUG') == 'true' or
    'localhost' in os.environ.get('DATABASE_URL', '') or
    'postgres:' in os.environ.get('DATABASE_URL', '')
)
```

### Environment Template

```bash
# env-devcontainer.example

# Development mode
NODE_ENV=development
DEBUG=true

# Database - use service name, not localhost
DATABASE_URL=postgresql://postgres:password@postgres:5432/app

# Cache
REDIS_URL=redis://valkey:6379

# S3-compatible storage
SPACES_ENDPOINT=http://minio:9000
SPACES_KEY_ID=rustfsadmin
SPACES_SECRET_KEY=rustfsadmin
```

---

## VS Code Extensions by Language

Add to `.devcontainer/devcontainer.json`:

```json
"customizations": {
  "vscode": {
    "extensions": [
      // Always useful
      "ms-azuretools.vscode-docker",
      "GitHub.copilot",

      // JavaScript/TypeScript
      "dbaeumer.vscode-eslint",
      "esbenp.prettier-vscode",

      // Python
      "ms-python.python",
      "ms-python.vscode-pylance",

      // Go
      "golang.go",

      // Rust
      "rust-lang.rust-analyzer"
    ]
  }
}
```
