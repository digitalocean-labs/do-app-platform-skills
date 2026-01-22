"""Tests for shared configurations."""

import pytest
import yaml
from pathlib import Path


class TestSharedConfigurations:
    """Tests for shared YAML configurations."""

    def test_regions_yaml_valid(self, shared_config_dir):
        """regions.yaml should be valid."""
        with open(shared_config_dir / "regions.yaml") as f:
            data = yaml.safe_load(f)
        assert "regions" in data
        assert len(data["regions"]) > 0

    def test_regions_have_required_fields(self, shared_config_dir):
        """Each region should have slug and name."""
        with open(shared_config_dir / "regions.yaml") as f:
            data = yaml.safe_load(f)
        for region in data["regions"]:
            assert "slug" in region
            assert "name" in region

    def test_instance_sizes_valid(self, shared_config_dir):
        """instance-sizes.yaml should be valid."""
        with open(shared_config_dir / "instance-sizes.yaml") as f:
            data = yaml.safe_load(f)
        assert "sizes" in data
        assert "shared" in data["sizes"]
        assert "dedicated" in data["sizes"]

    def test_opinionated_defaults_valid(self, shared_config_dir):
        """opinionated-defaults.yaml should be valid."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        assert "region" in data
        assert "database" in data
        assert "cache" in data

    def test_cache_defaults_to_valkey(self, shared_config_dir):
        """Cache should default to Valkey, not Redis."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        assert data["cache"]["engine"] == "VALKEY"

    def test_ssl_mode_is_require(self, shared_config_dir):
        """SSL mode should be require."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        assert data["database"]["ssl_mode"] == "require"
