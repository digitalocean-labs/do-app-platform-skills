"""Shared pytest fixtures."""

import pytest
from pathlib import Path


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
def shared_config_dir():
    """Return path to shared configuration directory."""
    return Path(__file__).parent.parent / "shared"
