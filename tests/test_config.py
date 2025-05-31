import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any
from src.config.loader import ConfigManager, load_gitignore_patterns

def test_load_config():
    """Test loading configuration from YAML file."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config_manager.config_path = config_path
    
    # Only run this test if config file exists
    if os.path.exists(config_path):
        # Directly load the file for testing
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set the config in the config manager
        config_manager.config = config
        
        assert "platforms" in config_manager.config
        assert "general" in config_manager.config or isinstance(config_manager.config.get("platforms"), dict)
        
        # Test platform retrieval
        if "cursor" in config_manager.config.get("platforms", {}):
            platform_config = config_manager.get_platform_config("cursor")
            assert isinstance(platform_config, dict)
            
            # Check basic structure
            assert "project_path" in platform_config
            # Other assertions as needed...

def test_validate_platform_config():
    """Test platform configuration validation."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    # Only run this test if config file exists
    if os.path.exists(config_path):
        # Load config for testing
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config_manager.config = config
        
        if "cursor" in config_manager.config.get("platforms", {}):
            cursor_config = config_manager.get_platform_config("cursor")
            
            # Validate key fields
            assert "project_path" in cursor_config, "Missing project_path in cursor config"
            assert "task_file_path" in cursor_config, "Missing task_file_path in cursor config"
            
            # More validations as needed...

def test_get_active_platforms():
    """Test retrieving active platforms from config."""
    config_manager = ConfigManager()
    
    # Create test config
    test_config = {
        "general": {
            "active_platforms": ["cursor", "windsurf"]
        },
        "platforms": {
            "cursor": {"project_path": "/test/cursor"},
            "windsurf": {"project_path": "/test/windsurf"},
            "inactive": {"project_path": "/test/inactive"}
        }
    }
    config_manager.config = test_config
    
    # Create test args
    class Args:
        platform = None
    
    args = Args()
    
    # Get active platforms from general config
    active_platforms = config_manager.get_active_platforms(args)
    assert active_platforms == ["cursor", "windsurf"]
    assert "inactive" not in active_platforms
    
    # Test command-line override
    args.platform = "cursor"
    active_platforms = config_manager.get_active_platforms(args)
    assert active_platforms == ["cursor"]
    assert "windsurf" not in active_platforms
    
    # Test comma-separated platforms
    args.platform = "cursor,windsurf"
    active_platforms = config_manager.get_active_platforms(args)
    assert "cursor" in active_platforms
    assert "windsurf" in active_platforms
    
    # Test invalid platform
    args.platform = "invalid"
    active_platforms = config_manager.get_active_platforms(args)
    assert active_platforms == []

def test_gitignore_patterns():
    """Test loading gitignore patterns."""
    # Create a temporary directory and gitignore file
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        gitignore_path = os.path.join(tmpdir, ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write("*.pyc\nnode_modules/\n__pycache__/\n")
        
        # Load patterns using the module-level function
        patterns = load_gitignore_patterns(tmpdir)
        
        # Verify patterns were loaded
        assert "*.pyc" in patterns
        assert "node_modules" in patterns
        assert "__pycache__" in patterns

def test_platform_specific_keystrokes():
    """Test platform-specific keystroke mapping."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    # Skip test if config file doesn't exist
    if not os.path.exists(config_path):
        pytest.skip("Config file not found")
    
    # Load config for testing
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config_manager.config = config
    
    # Continue only if cursor config exists
    if "cursor" not in config["platforms"]:
        pytest.skip("Cursor platform not found in config")
    
    cursor_config = config_manager.get_platform_config("cursor")
    
    # Test initialization keystrokes if they exist
    if "initialization" in cursor_config:
        for keystroke in cursor_config["initialization"]:
            assert "keys" in keystroke
            assert "delay_ms" in keystroke
            assert isinstance(keystroke["delay_ms"], int)
            assert keystroke["delay_ms"] > 0

def test_vision_conditions():
    """Test OpenAI Vision conditions configuration."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    # Skip test if config file doesn't exist
    if not os.path.exists(config_path):
        pytest.skip("Config file not found")
    
    # Load config for testing
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config_manager.config = config
    
    # Continue only if cursor config exists
    if "cursor" not in config["platforms"]:
        pytest.skip("Cursor platform not found in config")
    
    cursor_config = config_manager.get_platform_config("cursor")
    vision_conditions = cursor_config.get("options", {}).get("vision_conditions", [])
    
    for condition in vision_conditions:
        assert "file_type" in condition
        assert "action" in condition
        assert "question" in condition
        
        # Test keystroke configurations if they exist
        for keystroke_list in ["success_keystrokes", "failure_keystrokes"]:
            if keystroke_list in condition:
                for keystroke in condition[keystroke_list]:
                    assert "keys" in keystroke
                    if "delay_ms" in keystroke:
                        assert isinstance(keystroke["delay_ms"], int)
                        assert keystroke["delay_ms"] > 0

def test_slack_config():
    """Test Slack configuration."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    # Skip test if config file doesn't exist
    if not os.path.exists(config_path):
        pytest.skip("Config file not found")
    
    # Load config for testing
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config_manager.config = config
    
    # Skip if slack section doesn't exist
    if "slack" not in config:
        pytest.skip("Slack configuration not found")
    
    slack_config = config["slack"]
    assert "enabled" in slack_config
    
    # Only check the rest if slack is enabled
    if slack_config.get("enabled", False):
        assert "bot_token" in slack_config
        assert "channels" in slack_config
        
        # Test channel configuration if channels exist
        if "channels" in slack_config and slack_config["channels"]:
            for channel in slack_config["channels"]:
                assert "name" in channel
                assert "id" in channel

def test_openai_config():
    """Test OpenAI configuration."""
    config_manager = ConfigManager()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    # Skip test if config file doesn't exist
    if not os.path.exists(config_path):
        pytest.skip("Config file not found")
    
    # Load config for testing
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config_manager.config = config
    
    # Skip if openai section doesn't exist
    if "openai" not in config or "vision" not in config["openai"]:
        pytest.skip("OpenAI vision configuration not found")
    
    openai_config = config["openai"]["vision"]
    assert "enabled" in openai_config
    
    # Only check the rest if vision is enabled
    if openai_config.get("enabled", False):
        assert "model" in openai_config
        
        # Check required fields conditionally
        if "api_key" in openai_config:
            assert isinstance(openai_config["api_key"], str)
        
        if "max_tokens" in openai_config:
            assert isinstance(openai_config["max_tokens"], int)
        
        if "temperature" in openai_config:
            assert 0 <= openai_config["temperature"] <= 1 