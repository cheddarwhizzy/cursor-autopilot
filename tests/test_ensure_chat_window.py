import os
import pytest
from unittest.mock import patch, MagicMock
import logging
from src.ensure_chat_window import ensure_chat_window, get_config

# Configure logging
logger = logging.getLogger('ensure_chat_window')

@pytest.fixture
def mock_config():
    return {
        "platform": "cursor",
        "use_vision_api": True
    }

@pytest.fixture
def mock_vision_response():
    return True

def test_get_config(tmp_path):
    # Create a temporary config file
    config_path = tmp_path / "config.yaml"
    config_content = """
    platform: cursor
    use_vision_api: true
    """
    config_path.write_text(config_content)
    
    with patch('src.ensure_chat_window.os.path.join', return_value=str(config_path)):
        config = get_config()
        assert config["platform"] == "cursor"
        assert config["use_vision_api"] is True

def test_get_config_missing_file():
    with patch('src.ensure_chat_window.os.path.join', return_value="/nonexistent/config.yaml"):
        config = get_config()
        assert config == {}

@patch('src.ensure_chat_window.get_config')
@patch('src.ensure_chat_window.kill_cursor')
@patch('src.ensure_chat_window.launch_platform')
@patch('src.ensure_chat_window.take_cursor_screenshot')
@patch('src.ensure_chat_window.is_chat_window_open')
@patch('src.ensure_chat_window.send_keys')
def test_ensure_chat_window_with_vision(
    mock_send_keys,
    mock_is_chat_window_open,
    mock_take_screenshot,
    mock_launch_platform,
    mock_kill_cursor,
    mock_get_config,
    mock_config
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_take_screenshot.return_value = "/tmp/screenshot.png"
    mock_is_chat_window_open.return_value = True

    # Call function
    ensure_chat_window()

    # Verify function calls
    mock_kill_cursor.assert_called_once_with("cursor")
    mock_launch_platform.assert_called_once_with(
        "cursor", mock_config.get("project_path")
    )
    mock_take_screenshot.assert_called_once_with(platform="cursor")
    mock_is_chat_window_open.assert_called_once_with("/tmp/screenshot.png")
    mock_send_keys.assert_called_once_with(["command down", "l", "command up"], platform="cursor")

@patch('src.ensure_chat_window.get_config')
@patch('src.ensure_chat_window.kill_cursor')
@patch('src.ensure_chat_window.launch_platform')
@patch('src.ensure_chat_window.take_cursor_screenshot')
@patch('src.ensure_chat_window.is_chat_window_open')
@patch('src.ensure_chat_window.send_keys')
def test_ensure_chat_window_without_vision(
    mock_send_keys,
    mock_is_chat_window_open,
    mock_take_screenshot,
    mock_launch_platform,
    mock_kill_cursor,
    mock_get_config
):
    # Setup mocks
    mock_get_config.return_value = {"platform": "cursor", "use_vision_api": False}
    
    # Call function
    ensure_chat_window()
    
    # Verify function calls
    mock_kill_cursor.assert_called_once_with("cursor")
    mock_launch_platform.assert_called_once_with("cursor")
    mock_take_screenshot.assert_not_called()
    mock_is_chat_window_open.assert_not_called()
    mock_send_keys.assert_not_called()

@patch('src.ensure_chat_window.get_config')
@patch('src.ensure_chat_window.kill_cursor')
@patch('src.ensure_chat_window.launch_platform')
@patch('src.ensure_chat_window.take_cursor_screenshot')
@patch('src.ensure_chat_window.is_chat_window_open')
@patch('src.ensure_chat_window.send_keys')
def test_ensure_chat_window_with_windsurf(
    mock_send_keys,
    mock_is_chat_window_open,
    mock_take_screenshot,
    mock_launch_platform,
    mock_kill_cursor,
    mock_get_config
):
    # Setup mocks
    mock_get_config.return_value = {
        "platform": "windsurf",
        "use_vision_api": True,
        "project_path": "/test/path",
    }
    mock_take_screenshot.return_value = "/tmp/screenshot.png"
    mock_is_chat_window_open.return_value = False

    # Call function
    ensure_chat_window()

    # Verify function calls
    mock_kill_cursor.assert_called_once_with("windsurf")
    mock_launch_platform.assert_called_once_with("windsurf", "/test/path")
    mock_take_screenshot.assert_called_once_with(platform="windsurf")
    mock_is_chat_window_open.assert_called_once_with("/tmp/screenshot.png")
    mock_send_keys.assert_called_once_with(["command down", "l", "command up"], platform="windsurf")

@patch('src.ensure_chat_window.get_config')
@patch('src.ensure_chat_window.kill_cursor')
@patch('src.ensure_chat_window.launch_platform')
@patch('src.ensure_chat_window.take_cursor_screenshot')
@patch('src.ensure_chat_window.is_chat_window_open')
@patch('src.ensure_chat_window.send_keys')
def test_ensure_chat_window_screenshot_failure(
    mock_send_keys,
    mock_is_chat_window_open,
    mock_take_screenshot,
    mock_launch_platform,
    mock_kill_cursor,
    mock_get_config,
    mock_config
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_take_screenshot.return_value = None  # Simulate screenshot failure
    
    # Call function
    ensure_chat_window()
    
    # Verify function calls
    mock_kill_cursor.assert_called_once_with("cursor")
    mock_launch_platform.assert_called_once_with("cursor")
    mock_take_screenshot.assert_called_once_with(platform="cursor")
    mock_is_chat_window_open.assert_not_called()
    mock_send_keys.assert_not_called()

@patch('src.ensure_chat_window.get_config')
@patch('src.ensure_chat_window.kill_cursor')
@patch('src.ensure_chat_window.launch_platform')
@patch('src.ensure_chat_window.take_cursor_screenshot')
@patch('src.ensure_chat_window.is_chat_window_open')
@patch('src.ensure_chat_window.send_keys')
def test_ensure_chat_window_explicit_platform(
    mock_send_keys,
    mock_is_chat_window_open,
    mock_take_screenshot,
    mock_launch_platform,
    mock_kill_cursor,
    mock_get_config,
    mock_config
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_take_screenshot.return_value = "/tmp/screenshot.png"
    mock_is_chat_window_open.return_value = True

    # Call function with explicit platform
    ensure_chat_window(platform="windsurf")

    # Verify function calls use explicit platform
    mock_kill_cursor.assert_called_once_with("windsurf")
    mock_launch_platform.assert_called_once_with(
        "windsurf", mock_config.get("project_path")
    )
    mock_take_screenshot.assert_called_once_with(platform="windsurf")
    mock_is_chat_window_open.assert_called_once_with("/tmp/screenshot.png")
    mock_send_keys.assert_called_once_with(["command down", "l", "command up"], platform="windsurf") 
