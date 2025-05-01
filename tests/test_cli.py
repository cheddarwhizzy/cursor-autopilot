import os
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
    """Test command line argument parsing."""
    # Test with no arguments
    with patch.object(sys, 'argv', ['cli.py']):
        args = parse_args()
        assert args.project_path is None
        assert args.platform is None
        assert args.inactivity_delay is None
        assert args.send_message is None
        assert args.debug is None
        assert args.config == "config.yaml"
    
    # Test with all arguments
    test_args = [
        'cli.py',
        '--project-path', '/test/path',
        '--platform', 'cursor,windsurf',
        '--inactivity-delay', '300',
        '--send-message',
        '--debug',
        '--config', 'test_config.yaml'
    ]
    with patch.object(sys, 'argv', test_args):
        args = parse_args()
        assert args.project_path == '/test/path'
        assert args.platform == 'cursor,windsurf'
        assert args.inactivity_delay == 300
        assert args.send_message is True
        assert args.debug is True
        assert args.config == 'test_config.yaml'

def test_parse_args_edge_cases():
    """Test edge cases in command line argument parsing."""
    # Test with empty platform
    with patch.object(sys, 'argv', ['cli.py', '--platform', '']):
        args = parse_args()
        assert args.platform == ''
    
    # Test with negative inactivity delay
    with patch.object(sys, 'argv', ['cli.py', '--inactivity-delay', '-1']):
        args = parse_args()
        assert args.inactivity_delay == -1
    
    # Test with non-existent config file
    with patch.object(sys, 'argv', ['cli.py', '--config', 'nonexistent.yaml']):
        args = parse_args()
        assert args.config == 'nonexistent.yaml'

def test_merge_configs():
    """Test merging of config file and command line arguments."""
    config = {
        "project_path": "/default/path",
        "platform": "cursor",
        "inactivity_delay": 300,
        "send_message": False,
        "debug": False
    }
    
    class Args:
        project_path = "/cli/path"
        platform = "windsurf"
        inactivity_delay = 600
        send_message = True
        debug = True
        config = "config.yaml"
    
    merged = merge_configs(config, Args())
    assert merged["project_path"] == "/cli/path"
    assert merged["platform"] == "windsurf"
    assert merged["inactivity_delay"] == 600
    assert merged["send_message"] is True
    assert merged["debug"] is True

def test_merge_configs_edge_cases():
    """Test edge cases in config merging."""
    # Test with empty config
    config = {}
    args = type('Args', (), {
        'project_path': '/test/path',
        'platform': 'cursor',
        'inactivity_delay': 300,
        'send_message': True,
        'debug': True,
        'config': 'config.yaml'
    })
    merged = merge_configs(config, args)
    assert merged == {
        'project_path': '/test/path',
        'platform': 'cursor',
        'inactivity_delay': 300,
        'send_message': True,
        'debug': True
    }
    
    # Test with None values in args
    config = {
        'project_path': '/default/path',
        'platform': 'cursor',
        'inactivity_delay': 300
    }
    args = type('Args', (), {
        'project_path': None,
        'platform': None,
        'inactivity_delay': None,
        'send_message': None,
        'debug': None,
        'config': 'config.yaml'
    })
    merged = merge_configs(config, args)
    assert merged == config

def test_validate_config():
    """Test configuration validation."""
    # Test valid config with platform list
    valid_config = {
        "project_path": "/test/path",
        "platform": ["cursor", "windsurf"],
        "inactivity_delay": 300
    }
    assert validate_config(valid_config) is True
    
    # Test valid config with single platform
    valid_single_config = {
        "project_path": "/test/path",
        "platform": "cursor",
        "inactivity_delay": 300
    }
    assert validate_config(valid_single_config) is True
    
    # Test invalid platform
    invalid_platform_config = {
        "project_path": "/test/path",
        "platform": ["cursor", "invalid"],
        "inactivity_delay": 300
    }
    assert validate_config(invalid_platform_config) is False
    
    # Test missing required field
    missing_field_config = {
        "platform": ["cursor", "windsurf"]
    }
    assert validate_config(missing_field_config) is False
    
    # Test invalid project path
    invalid_path_config = {
        "project_path": "/nonexistent/path",
        "platform": ["cursor", "windsurf"],
        "inactivity_delay": 300
    }
    with patch("os.path.isdir", return_value=False):
        assert validate_config(invalid_path_config) is False

def test_validate_config_edge_cases():
    """Test edge cases in configuration validation."""
    # Test with empty platform list
    config = {
        'project_path': '/test/path',
        'platform': '',
        'inactivity_delay': 300
    }
    with patch('os.path.isdir', return_value=True):
        assert validate_config(config) is False
    
    # Test with whitespace in platform list
    config = {
        'project_path': '/test/path',
        'platform': 'cursor, windsurf',
        'inactivity_delay': 300
    }
    with patch('os.path.isdir', return_value=True):
        assert validate_config(config) is True
    
    # Test with invalid project path format
    config = {
        'project_path': 'relative/path',
        'platform': 'cursor',
        'inactivity_delay': 300
    }
    with patch('os.path.isdir', return_value=True):
        assert validate_config(config) is False

def test_main():
    """Test main entry point."""
    # Test successful execution
    with patch("src.cli.parse_args") as mock_parse, \
         patch("src.cli.load_config") as mock_load, \
         patch("src.cli.merge_configs") as mock_merge, \
         patch("src.cli.validate_config", return_value=True), \
         patch("logging.getLogger") as mock_logger:
        
        mock_parse.return_value = type('Args', (), {
            'config': 'test_config.yaml',
            'project_path': None,
            'platform': None,
            'inactivity_delay': None,
            'send_message': None,
            'debug': None
        })
        mock_load.return_value = {
            "project_path": "/test/path",
            "platform": "cursor",
            "inactivity_delay": 300
        }
        mock_merge.return_value = mock_load.return_value
        
        assert main() == 0
    
    # Test validation failure
    with patch("src.cli.parse_args") as mock_parse, \
         patch("src.cli.load_config") as mock_load, \
         patch("src.cli.merge_configs") as mock_merge, \
         patch("src.cli.validate_config", return_value=False):
        
        mock_parse.return_value = type('Args', (), {
            'config': 'test_config.yaml',
            'project_path': None,
            'platform': None,
            'inactivity_delay': None,
            'send_message': None,
            'debug': None
        })
        mock_load.return_value = {
            "project_path": "/test/path",
            "platform": "cursor",
            "inactivity_delay": 300
        }
        mock_merge.return_value = mock_load.return_value
        
        assert main() == 1

def test_main_edge_cases():
    """Test edge cases in main entry point."""
    # Test with environment variable conflicts
    with patch('os.environ', {
        'CURSOR_AUTOPILOT_PROJECT_PATH': '/env/path',
        'CURSOR_AUTOPILOT_PLATFORM': 'cursor',
        'CURSOR_AUTOPILOT_AUTO_MODE': '1',
        'CURSOR_AUTOPILOT_SEND_MESSAGE': 'true',
        'CURSOR_AUTOPILOT_DEBUG': 'true'
    }), \
    patch('src.cli.parse_args') as mock_parse, \
    patch('src.cli.load_config') as mock_load, \
    patch('src.cli.merge_configs') as mock_merge, \
    patch('src.cli.validate_config', return_value=True), \
    patch('logging.getLogger') as mock_logger:
        
        mock_parse.return_value = type('Args', (), {
            'config': 'test_config.yaml',
            'project_path': '/cli/path',
            'platform': 'windsurf',
            'inactivity_delay': 300,
            'send_message': False,
            'debug': False
        })
        mock_load.return_value = {
            'project_path': '/config/path',
            'platform': 'cursor',
            'inactivity_delay': 300
        }
        mock_merge.return_value = mock_parse.return_value.__dict__
        
        assert main() == 0
    
    # Test with logging errors
    with patch('src.cli.parse_args') as mock_parse, \
         patch('src.cli.load_config') as mock_load, \
         patch('src.cli.merge_configs') as mock_merge, \
         patch('src.cli.validate_config', return_value=True), \
         patch('logging.getLogger', side_effect=Exception('Logging error')):
        
        mock_parse.return_value = type('Args', (), {
            'config': 'test_config.yaml',
            'project_path': '/test/path',
            'platform': 'cursor',
            'inactivity_delay': 300
        })
        mock_load.return_value = {}
        mock_merge.return_value = mock_parse.return_value.__dict__
        
        assert main() == 0  # Should still succeed despite logging error 