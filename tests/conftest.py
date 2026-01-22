"""Shared pytest fixtures."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock
import json


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository directory."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    return repo_dir


@pytest.fixture
def heroku_repo(temp_repo):
    """Create a Heroku-style repository."""
    (temp_repo / "Procfile").write_text("web: python app.py\nworker: python worker.py")
    (temp_repo / "requirements.txt").write_text("flask>=2.0")
    return temp_repo


@pytest.fixture
def docker_compose_repo(temp_repo):
    """Create a Docker Compose repository."""
    compose = """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:8080"
  postgres:
    image: postgres:15
"""
    (temp_repo / "docker-compose.yml").write_text(compose)
    (temp_repo / "Dockerfile").write_text("FROM python:3.12")
    return temp_repo


@pytest.fixture
def nodejs_repo(temp_repo):
    """Create a Node.js repository."""
    package_json = {
        "name": "test-app",
        "version": "1.0.0",
        "scripts": {
            "start": "node server.js",
            "build": "webpack"
        },
        "dependencies": {
            "express": "^4.18.0"
        }
    }
    (temp_repo / "package.json").write_text(json.dumps(package_json, indent=2))
    (temp_repo / "server.js").write_text("console.log('Hello World');")
    return temp_repo


@pytest.fixture
def nextjs_repo(temp_repo):
    """Create a Next.js repository."""
    package_json = {
        "name": "nextjs-app",
        "version": "0.1.0",
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start"
        },
        "dependencies": {
            "next": "14.0.0",
            "react": "18.2.0"
        }
    }
    (temp_repo / "package.json").write_text(json.dumps(package_json, indent=2))
    (temp_repo / "next.config.js").write_text("module.exports = {}")
    return temp_repo


@pytest.fixture
def python_fastapi_repo(temp_repo):
    """Create a Python FastAPI repository."""
    (temp_repo / "requirements.txt").write_text(
        "fastapi>=0.100.0\nuvicorn[standard]>=0.23.0\npydantic>=2.0.0"
    )
    (temp_repo / "main.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n"
        "@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}"
    )
    return temp_repo


@pytest.fixture
def monorepo(temp_repo):
    """Create a monorepo structure."""
    # Frontend
    frontend = temp_repo / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"name": "frontend", "dependencies": {"react": "^18.0.0"}}')
    
    # Backend
    backend = temp_repo / "backend"
    backend.mkdir()
    (backend / "requirements.txt").write_text("fastapi>=0.100.0")
    (backend / "main.py").write_text("# FastAPI app")
    
    return temp_repo


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def shared_config_dir():
    """Return path to shared configuration directory."""
    return Path(__file__).parent.parent / "shared"


@pytest.fixture
def sample_app_spec():
    """Sample valid app spec for testing."""
    return {
        "spec": {
            "name": "test-app",
            "region": "nyc",
            "services": [
                {
                    "name": "web",
                    "github": {
                        "repo": "user/repo",
                        "branch": "main"
                    },
                    "run_command": "python app.py",
                    "instance_size_slug": "apps-s-1vcpu-1gb",
                    "http_port": 8080
                }
            ],
            "databases": [
                {
                    "name": "db",
                    "engine": "PG",
                    "version": "16"
                }
            ]
        }
    }


@pytest.fixture
def sample_connection_strings():
    """Sample database connection strings for testing."""
    return {
        "postgres": "postgresql://user:pass@host.db.ondigitalocean.com:25060/db?sslmode=require",
        "mysql": "mysql://user:pass@host.db.ondigitalocean.com:25060/db?ssl-mode=REQUIRED",
        "mongodb": "mongodb+srv://user:pass@host.db.ondigitalocean.com/db?tls=true",
        "valkey": "rediss://default:pass@host.db.ondigitalocean.com:25061",
    }


@pytest.fixture
def sample_env_vars():
    """Sample environment variables for testing."""
    return {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
        "SECRET_KEY": "test-secret-key",
        "API_KEY": "test-api-key",
        "PORT": "8080",
        "DEBUG": "False",
    }


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_psycopg2():
    """Mock psycopg2 for database tests."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    return {
        "connection": mock_conn,
        "cursor": mock_cursor
    }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for command execution tests."""
    mock = MagicMock()
    mock.run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mock.CalledProcessError = Exception
    return mock


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    return {
        "repo": {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "default_branch": "main",
            "private": False
        },
        "secrets": [
            {"name": "DATABASE_URL"},
            {"name": "SECRET_KEY"}
        ]
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def valid_region_slugs():
    """Valid DigitalOcean region slugs."""
    return ["nyc", "nyc1", "nyc3", "sfo", "sfo2", "sfo3", "ams", "ams3", 
            "lon", "lon1", "fra", "fra1", "sgp", "sgp1", "blr", "blr1", 
            "tor", "tor1", "syd", "syd1"]


@pytest.fixture
def valid_db_engines():
    """Valid database engine types."""
    return ["PG", "MYSQL", "MONGODB", "VALKEY", "REDIS", "KAFKA", "OPENSEARCH"]


@pytest.fixture
def platform_indicators():
    """Platform detection indicators."""
    return {
        "heroku": ["Procfile", "app.json"],
        "render": ["render.yaml"],
        "fly": ["fly.toml"],
        "railway": ["railway.json"],
        "docker": ["Dockerfile", "docker-compose.yml"]
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def skip_if_no_internet():
    """Skip test if no internet connection."""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
    except OSError:
        pytest.skip("No internet connection available")


@pytest.fixture
def skip_if_no_psycopg2():
    """Skip test if psycopg2 is not installed."""
    try:
        import psycopg2
    except ImportError:
        pytest.skip("psycopg2 not installed")
