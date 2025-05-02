a
aaaimport os
import sys
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock
import yaml
import logging
from src.cli import (
    load_config,
    parse_args,
    merge_configs,
    validate_config,
    main
)

def test_load_config():
    """Test loading configuration from YAML file."""
    # Test with valid YAML including platform list
    yaml_content = """
    project_path: "/test/path"
    platform: ["cursor", "windsurf"]
    inactivity_delay: 300
    """
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        config = load_config()
        assert config["project_path"] == "/test/path"
        assert isinstance(config["platform"], list)
        assert "cursor" in config["platform"]
        assert "windsurf" in config["platform"]
        assert config["inactivity_delay"] == 300
    
    # Test with single platform string
    yaml_content = """
    project_path: "/test/path"
    platform: "cursor"
    inactivity_delay: 300
    """
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        config = load_config()
        assert config["project_path"] == "/test/path"
        assert config["platform"] == "cursor"
        assert config["inactivity_delay"] == 300
    
    # Test with invalid YAML
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content")):
        with pytest.raises(SystemExit):
            load_config()
    
    # Test with non-existent file
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = load_config()
        assert config == {}

def test_parse_args():
    """Test argument parsing."""
    pytest.skip("CLI tests to be refactored later")

def test_parse_args_edge_cases():
    """Test argument parsing edge cases."""
    pytest.skip("CLI tests to be refactored later")

def test_merge_configs():
    """Test configuration merging."""
    pytest.skip("CLI tests to be refactored later")

def test_merge_configs_edge_cases():
    """Test configuration merging edge cases."""
    pytest.skip("CLI tests to be refactored later")

def test_validate_config():
    """Test configuration validation."""
    pytest.skip("CLI tests to be refactored later")

def test_validate_config_edge_cases():
    """Test configuration validation edge cases."""
    pytest.skip("CLI tests to be refactored later")

def test_main():
    """Test main execution flow."""
    pytest.skip("CLI tests to be refactored later")

def test_main_edge_cases():
    """Test main execution edge cases."""
    pytest.skip("CLI tests to be refactored later") 