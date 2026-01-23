# Testing Guide

This guide covers how to run, write, and maintain tests for the DO App Platform Skills repository.

## Quick Start

```bash
# Install dependencies
make install

# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories
make test-unit
make test-integration
make test-security
```

## Test Organization

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_helpers.py          # Test utility functions
├── test_migration/          # Migration script tests
├── test_postgres/           # PostgreSQL script tests
├── test_shared/             # Shared configuration tests
├── test_validation/         # Schema and doc validation tests
├── test_workflows/          # End-to-end workflow tests
├── test_edge_cases/         # Error handling tests
└── test_security/           # Security tests
```

### Test Categories (Markers)

Tests are organized using pytest markers:

- **`@pytest.mark.unit`** - Fast, isolated unit tests
- **`@pytest.mark.integration`** - Integration tests (may need external resources)
- **`@pytest.mark.security`** - Security-focused tests
- **`@pytest.mark.validation`** - Configuration/schema validation tests
- **`@pytest.mark.e2e`** - End-to-end workflow tests
- **`@pytest.mark.slow`** - Slow-running tests
- **`@pytest.mark.requires_network`** - Tests requiring internet
- **`@pytest.mark.requires_db`** - Tests requiring database connection

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_migration/test_detect_platform.py

# Run specific test class
pytest tests/test_migration/test_detect_platform.py::TestPlatformDetector

# Run specific test
pytest tests/test_migration/test_detect_platform.py::TestPlatformDetector::test_detects_heroku_from_procfile
```

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run security tests
pytest -m security

# Exclude slow tests
pytest -m "not slow"

# Run multiple categories
pytest -m "unit or integration"
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=skills --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=skills --cov-report=html
open htmlcov/index.html

# Generate XML coverage (for CI)
pytest --cov=skills --cov-report=xml
```

### Using Make Commands

```bash
make help           # Show all available commands
make test           # Run all tests
make test-cov       # Run tests with coverage
make test-html      # Run tests and open HTML coverage report
make test-unit      # Run unit tests only
make test-fast      # Skip slow tests
make clean          # Clean up generated files
```

## Writing Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

```python
# tests/test_migration/test_my_feature.py

@pytest.mark.unit
class TestMyFeature:
    """Tests for my feature."""
    
    def test_basic_functionality(self):
        """Should perform basic operation."""
        result = my_feature()
        assert result == expected_value
    
    @pytest.mark.slow
    def test_complex_operation(self):
        """Should handle complex scenarios."""
        # ... test code
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

```python
def test_with_temp_repo(temp_repo):
    """Test using temporary repository."""
    # temp_repo is a Path to empty directory
    (temp_repo / "file.txt").write_text("content")
    assert (temp_repo / "file.txt").exists()

def test_with_heroku_repo(heroku_repo):
    """Test using Heroku-style repository."""
    # heroku_repo has Procfile and requirements.txt
    assert (heroku_repo / "Procfile").exists()

def test_with_sample_data(sample_app_spec, sample_connection_strings):
    """Test using sample data."""
    assert "spec" in sample_app_spec
    assert "postgres" in sample_connection_strings
```

### Available Fixtures

#### Repository Fixtures
- `temp_repo` - Empty temporary directory
- `heroku_repo` - Heroku-style app
- `docker_compose_repo` - Docker Compose app
- `nodejs_repo` - Node.js app
- `nextjs_repo` - Next.js app
- `python_fastapi_repo` - FastAPI app
- `monorepo` - Monorepo structure

#### Configuration Fixtures
- `shared_config_dir` - Path to shared configs
- `sample_app_spec` - Sample valid app spec
- `sample_connection_strings` - Sample DB connection strings
- `sample_env_vars` - Sample environment variables

#### Mock Fixtures
- `mock_psycopg2` - Mock database connection
- `mock_subprocess` - Mock subprocess execution
- `mock_github_api` - Mock GitHub API responses

#### Utility Fixtures
- `skip_if_no_internet` - Skip test if offline
- `skip_if_no_psycopg2` - Skip if psycopg2 not installed

### Test Helpers

Use helper functions from `test_helpers.py`:

```python
from test_helpers import (
    create_test_file,
    create_procfile,
    assert_valid_app_spec,
    assert_valid_connection_string,
    assert_sql_safe
)

def test_with_helpers(temp_repo):
    """Test using helper functions."""
    # Create files easily
    create_procfile(temp_repo, {"web": "python app.py"})
    
    # Validate outputs
    spec = generate_app_spec()
    assert_valid_app_spec(spec)
    
    # Check SQL safety
    sql = generate_sql("schema", "user", "pass")
    assert_sql_safe(sql)
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

@patch('my_module.subprocess.run')
def test_with_mock(mock_run):
    """Test with mocked subprocess."""
    mock_run.return_value = MagicMock(returncode=0, stdout="success")
    
    result = my_function()
    
    assert result == "success"
    mock_run.assert_called_once()
```

## Best Practices

### 1. Test Independence
- Tests should not depend on each other
- Use fixtures for setup/teardown
- Clean up resources after tests

### 2. Clear Test Names
```python
# Good
def test_detects_heroku_from_procfile():
    """Should detect Heroku platform from Procfile."""

# Bad
def test_detection():
    """Test detection."""
```

### 3. Single Assertion Concept
Each test should verify one specific behavior:

```python
# Good - focused test
def test_creates_schema(self):
    sql = generate_sql("schema", "user", "pass")
    assert "CREATE SCHEMA" in sql

def test_creates_user(self):
    sql = generate_sql("schema", "user", "pass")
    assert "CREATE USER" in sql

# Less ideal - multiple concepts
def test_generates_everything(self):
    sql = generate_sql("schema", "user", "pass")
    assert "CREATE SCHEMA" in sql
    assert "CREATE USER" in sql
    assert "GRANT" in sql
```

### 4. Use Markers Appropriately
```python
@pytest.mark.unit  # Fast, isolated
def test_password_generation():
    password = generate_password(32)
    assert len(password) == 32

@pytest.mark.integration  # Requires resources
def test_database_setup(mock_psycopg2):
    setup_database(connection)

@pytest.mark.slow  # Takes >1 second
def test_large_repository():
    analyze_repo(large_repo_path)
```

### 5. Test Error Cases
```python
def test_handles_invalid_input(self):
    with pytest.raises(ValueError, match="Invalid input"):
        process_data("invalid")

def test_handles_missing_file(self):
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path")
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

The workflow:
1. Tests on multiple OS (Ubuntu, macOS)
2. Tests on multiple Python versions (3.11, 3.12, 3.13)
3. Generates coverage reports
4. Uploads to Codecov

### Local CI Simulation

```bash
# Run the full CI pipeline locally
make ci
```

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Migration scripts | 80%+ | ~75% |
| PostgreSQL scripts | 80%+ | ~70% |
| Shared configs | 90%+ | ~95% |
| Overall | 70%+ | ~70% |

## Troubleshooting

### Tests Fail on Import

```bash
# Make sure you're in venv and dependencies are installed
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Coverage Not Working

```bash
# Make sure pytest-cov is installed
pip install pytest-cov

# Check .coveragerc exists
ls -la .coveragerc
```

### Slow Test Suite

```bash
# Skip slow tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

### Import Errors in Tests

```python
# Add parent directory to path in test file
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
```

## Adding New Tests

1. **Choose the right directory** based on what you're testing
2. **Use existing fixtures** when possible
3. **Add appropriate markers** to categorize the test
4. **Write descriptive docstrings**
5. **Ensure tests are isolated** and don't depend on each other
6. **Run tests locally** before committing

Example:

```python
# tests/test_migration/test_new_feature.py
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))

from new_feature import process


@pytest.mark.unit
class TestNewFeature:
    """Tests for new feature functionality."""
    
    def test_basic_processing(self, temp_repo):
        """Should process basic input correctly."""
        result = process(temp_repo)
        assert result is not None
    
    @pytest.mark.integration
    def test_complex_scenario(self, heroku_repo):
        """Should handle complex scenarios."""
        result = process(heroku_repo, advanced=True)
        assert result["status"] == "success"
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures guide](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers guide](https://docs.pytest.org/en/stable/example/markers.html)
- [Coverage.py documentation](https://coverage.readthedocs.io/)

## Getting Help

If you have questions about testing:
1. Check this guide
2. Look at similar existing tests
3. Review pytest documentation
4. Ask in pull request discussions
