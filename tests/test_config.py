import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

def validate_platform_config(platform_config: Dict[str, Any]) -> None:
    """Validate platform-specific configuration."""
    required_fields = [
        "os_type",
        "project_path",
        "task_file_path",
        "additional_context_path",
        "initialization",
        "keystrokes",
        "options"
    ]
    
    for field in required_fields:
        if field not in platform_config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate os_type
    if platform_config["os_type"] not in ["osx", "windows", "linux"]:
        raise ValueError(f"Invalid os_type: {platform_config['os_type']}")
    
    # Validate project_path
    if not os.path.exists(platform_config["project_path"]):
        raise ValueError(f"Project path does not exist: {platform_config['project_path']}")
    
    # Validate initialization and keystrokes
    for keystroke_list in ["initialization", "keystrokes"]:
        if not isinstance(platform_config[keystroke_list], list):
            raise ValueError(f"{keystroke_list} must be a list")
        for keystroke in platform_config[keystroke_list]:
            if "keys" not in keystroke or "delay_ms" not in keystroke:
                raise ValueError(f"Invalid keystroke configuration: {keystroke}")
            if not isinstance(keystroke["delay_ms"], int):
                raise ValueError(f"delay_ms must be an integer: {keystroke['delay_ms']}")

def test_load_config():
    """Test loading configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    assert "platforms" in config
    assert "general" in config
    assert "slack" in config
    assert "openai" in config

def test_validate_platform_config():
    """Test platform configuration validation."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    # Test valid platform config
    cursor_config = config["platforms"]["cursor"]
    validate_platform_config(cursor_config)
    
    # Test invalid platform config
    invalid_config = {
        "os_type": "invalid",
        "project_path": "/nonexistent/path",
        "task_file_path": "tasks.md",
        "additional_context_path": "context.md",
        "initialization": [{"keys": "command+p"}],  # Missing delay_ms
        "keystrokes": [],
        "options": {}
    }
    
    with pytest.raises(ValueError) as exc_info:
        validate_platform_config(invalid_config)
    assert "Invalid os_type" in str(exc_info.value)

def test_platform_specific_keystrokes():
    """Test platform-specific keystroke mapping."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    cursor_config = config["platforms"]["cursor"]
    windsurf_config = config["platforms"]["windsurf"]
    
    # Test initialization keystrokes
    for platform_config in [cursor_config, windsurf_config]:
        for keystroke in platform_config["initialization"]:
            assert "keys" in keystroke
            assert "delay_ms" in keystroke
            assert isinstance(keystroke["delay_ms"], int)
            assert keystroke["delay_ms"] > 0

def test_vision_conditions():
    """Test OpenAI Vision conditions configuration."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    cursor_config = config["platforms"]["cursor"]
    vision_conditions = cursor_config["options"].get("vision_conditions", [])
    
    for condition in vision_conditions:
        assert "file_type" in condition
        assert "action" in condition
        assert "question" in condition
        assert "success_keystrokes" in condition
        assert "failure_keystrokes" in condition
        
        # Test keystroke configurations
        for keystroke_list in ["success_keystrokes", "failure_keystrokes"]:
            for keystroke in condition[keystroke_list]:
                assert "keys" in keystroke
                assert "delay_ms" in keystroke
                assert isinstance(keystroke["delay_ms"], int)
                assert keystroke["delay_ms"] > 0

def test_slack_config():
    """Test Slack configuration."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    slack_config = config["slack"]
    assert "enabled" in slack_config
    assert "bot_token" in slack_config
    assert "app_token" in slack_config
    assert "channels" in slack_config
    assert "commands" in slack_config
    
    # Test channel configuration
    for channel in slack_config["channels"]:
        assert "name" in channel
        assert "id" in channel
    
    # Test command configuration
    for command in slack_config["commands"]:
        assert "name" in command
        assert "description" in command

def test_openai_config():
    """Test OpenAI configuration."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config = load_config(config_path)
    
    openai_config = config["openai"]["vision"]
    assert "enabled" in openai_config
    assert "api_key" in openai_config
    assert "model" in openai_config
    assert "max_tokens" in openai_config
    assert "temperature" in openai_config
    assert "conditions" in openai_config
    
    # Test conditions configuration
    for condition in openai_config["conditions"]:
        assert "file_type" in condition
        assert "action" in condition
        assert "question" in condition 