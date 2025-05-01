import os
import pytest
from unittest.mock import patch, MagicMock
import logging
from src.state import get_mode, set_mode, get_config, STATE_FILE

# Configure logging
logger = logging.getLogger('state')

@pytest.fixture
def mock_config():
    return {
        "platform": "cursor",
        "use_vision_api": True
    }

def test_get_mode_no_file(tmp_path):
    # Test getting mode when state file doesn't exist
    with patch('src.state.STATE_FILE', str(tmp_path / STATE_FILE)):
        with patch.dict('os.environ', {'CURSOR_AUTOPILOT_AUTO_MODE': '1'}):
            assert get_mode() == "auto"
        
        with patch.dict('os.environ', {'CURSOR_AUTOPILOT_AUTO_MODE': '0'}):
            assert get_mode() == "code"
        
        with patch.dict('os.environ', {}):
            assert get_mode() == "code"

def test_get_mode_with_file(tmp_path):
    # Test getting mode from state file
    state_file = tmp_path / STATE_FILE
    state_file.write_text("auto")
    
    with patch('src.state.STATE_FILE', str(state_file)):
        assert get_mode() == "auto"

def test_set_mode(tmp_path):
    # Test setting mode
    state_file = tmp_path / STATE_FILE
    
    with patch('src.state.STATE_FILE', str(state_file)):
        set_mode("auto")
        assert state_file.read_text() == "auto"
        
        set_mode("code")
        assert state_file.read_text() == "code"

def test_get_config(tmp_path):
    # Create a temporary config file
    config_path = tmp_path / "config.yaml"
    config_content = """
    platform: cursor
    use_vision_api: true
    """
    config_path.write_text(config_content)
    
    with patch('src.state.os.path.join', return_value=str(config_path)):
        config = get_config()
        assert config["platform"] == "cursor"
        assert config["use_vision_api"] == True

def test_get_config_error():
    with patch('src.state.os.path.join', return_value="/nonexistent/path"):
        config = get_config()
        assert config == {} 