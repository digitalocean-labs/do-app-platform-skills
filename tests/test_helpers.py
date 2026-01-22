"""Pytest helpers and utilities for test suite."""

from pathlib import Path
from typing import Dict, Any, List
import json
import yaml


def create_test_file(directory: Path, filename: str, content: str) -> Path:
    """Create a test file with given content.
    
    Args:
        directory: Directory to create file in
        filename: Name of file to create
        content: Content to write to file
        
    Returns:
        Path to created file
    """
    filepath = directory / filename
    filepath.write_text(content)
    return filepath


def create_procfile(directory: Path, processes: Dict[str, str]) -> Path:
    """Create a Procfile with given processes.
    
    Args:
        directory: Directory to create Procfile in
        processes: Dict of process_name: command
        
    Returns:
        Path to created Procfile
    """
    content = "\n".join(f"{name}: {cmd}" for name, cmd in processes.items())
    return create_test_file(directory, "Procfile", content)


def create_package_json(directory: Path, name: str = "test-app", 
                       dependencies: Dict[str, str] = None,
                       scripts: Dict[str, str] = None) -> Path:
    """Create a package.json file.
    
    Args:
        directory: Directory to create package.json in
        name: Package name
        dependencies: Package dependencies
        scripts: NPM scripts
        
    Returns:
        Path to created package.json
    """
    package = {
        "name": name,
        "version": "1.0.0",
        "dependencies": dependencies or {},
        "scripts": scripts or {}
    }
    return create_test_file(directory, "package.json", json.dumps(package, indent=2))


def create_requirements_txt(directory: Path, packages: List[str]) -> Path:
    """Create a requirements.txt file.
    
    Args:
        directory: Directory to create requirements.txt in
        packages: List of package specifications
        
    Returns:
        Path to created requirements.txt
    """
    content = "\n".join(packages)
    return create_test_file(directory, "requirements.txt", content)


def create_dockerfile(directory: Path, base_image: str = "python:3.12",
                     commands: List[str] = None) -> Path:
    """Create a Dockerfile.
    
    Args:
        directory: Directory to create Dockerfile in
        base_image: Base Docker image
        commands: Additional Docker commands
        
    Returns:
        Path to created Dockerfile
    """
    lines = [f"FROM {base_image}"]
    if commands:
        lines.extend(commands)
    content = "\n".join(lines)
    return create_test_file(directory, "Dockerfile", content)


def create_docker_compose(directory: Path, services: Dict[str, Any]) -> Path:
    """Create a docker-compose.yml file.
    
    Args:
        directory: Directory to create docker-compose.yml in
        services: Services configuration
        
    Returns:
        Path to created docker-compose.yml
    """
    compose = {
        "version": "3.8",
        "services": services
    }
    content = yaml.dump(compose, default_flow_style=False)
    return create_test_file(directory, "docker-compose.yml", content)


def assert_valid_app_spec(spec: Dict[str, Any]) -> None:
    """Assert that app spec has valid structure.
    
    Args:
        spec: App spec to validate
        
    Raises:
        AssertionError: If spec is invalid
    """
    assert "spec" in spec, "Missing 'spec' key"
    assert "name" in spec["spec"], "Missing 'name' in spec"
    assert "region" in spec["spec"], "Missing 'region' in spec"
    
    # Validate name format
    name = spec["spec"]["name"]
    assert name.replace("-", "").replace("_", "").isalnum(), \
        f"Invalid app name format: {name}"
    
    # Validate region
    valid_regions = ["nyc", "sfo", "ams", "lon", "fra", "sgp", "blr", "tor", "syd"]
    region = spec["spec"]["region"]
    assert any(region.startswith(r) for r in valid_regions), \
        f"Invalid region: {region}"


def assert_valid_connection_string(conn_str: str, expected_engine: str = None) -> None:
    """Assert that connection string is valid.
    
    Args:
        conn_str: Connection string to validate
        expected_engine: Expected database engine (postgresql, mysql, etc.)
        
    Raises:
        AssertionError: If connection string is invalid
    """
    assert conn_str, "Connection string is empty"
    
    if expected_engine:
        assert conn_str.startswith(expected_engine), \
            f"Expected {expected_engine} connection string"
    
    # Should have user and host
    assert "@" in conn_str, "Missing host in connection string"
    assert ":" in conn_str, "Missing credentials in connection string"


def assert_sql_safe(sql: str) -> None:
    """Assert that SQL doesn't contain obvious injection attempts.
    
    Args:
        sql: SQL to validate
        
    Raises:
        AssertionError: If SQL appears dangerous
    """
    dangerous_patterns = [
        "; DROP TABLE",
        "; DELETE FROM",
        "OR 1=1",
        "' OR '1'='1",
    ]
    
    sql_upper = sql.upper()
    for pattern in dangerous_patterns:
        assert pattern not in sql_upper, \
            f"SQL contains dangerous pattern: {pattern}"


def count_sql_statements(sql: str) -> int:
    """Count number of SQL statements in string.
    
    Args:
        sql: SQL string
        
    Returns:
        Number of statements (semicolon-separated)
    """
    # Simple count by semicolons (not perfect but good enough for tests)
    return sql.count(";")


def extract_env_vars(text: str) -> List[str]:
    """Extract environment variable names from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of environment variable names
    """
    import re
    # Match ${VAR}, $VAR, or VAR= patterns
    patterns = [
        r'\$\{([A-Z_][A-Z0-9_]*)\}',  # ${VAR}
        r'\$([A-Z_][A-Z0-9_]*)',       # $VAR
        r'([A-Z_][A-Z0-9_]*)=',        # VAR=
    ]
    
    vars_found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        vars_found.update(matches)
    
    return sorted(list(vars_found))


def mock_file_system_error(error_type: str = "permission"):
    """Create a mock file system error for testing.
    
    Args:
        error_type: Type of error (permission, not_found, exists)
        
    Returns:
        Appropriate exception instance
    """
    if error_type == "permission":
        return PermissionError("Permission denied")
    elif error_type == "not_found":
        return FileNotFoundError("File not found")
    elif error_type == "exists":
        return FileExistsError("File already exists")
    else:
        return OSError(f"File system error: {error_type}")
