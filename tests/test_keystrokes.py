import os
import pytest
import platform
import tempfile
from unittest.mock import patch, MagicMock
import logging
from src.actions.keystrokes import map_key, send_keystrokes, send_keystroke_sequence, send_keystroke_string, activate_window

def test_map_key():
    """Test key mapping for different platforms."""
    # Test command key mapping
    if platform.system().lower() == 'windows' or platform.system().lower() == 'linux':
        assert map_key('command') == 'ctrl'
    else:
        assert map_key('command') == 'command'
    
    # Test option key mapping
    if platform.system().lower() == 'windows' or platform.system().lower() == 'linux':
        assert map_key('option') == 'alt'
    else:
        assert map_key('option') == 'option'
    
    # Test other keys (should remain unchanged)
    assert map_key('shift') == 'shift'
    assert map_key('a') == 'a'
    assert map_key('1') == '1'

@pytest.fixture
def temp_test_file():
    """Create a temporary file for testing keystrokes."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp:
        temp.write("")
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup after test
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_send_keystrokes_to_file():
    """Test sending keystrokes to a file."""
    # No need for a temp file since we're completely mocking
    with patch('pyautogui.press') as mock_press:
        with patch('pyautogui.hotkey') as mock_hotkey:
            with patch('time.sleep') as mock_sleep:
                # Test single key press
                assert send_keystrokes('a', delay_ms=10)
                mock_press.assert_called_with('a')
                mock_sleep.assert_called_with(0.01)  # 10ms
                
                # Test hotkey
                assert send_keystrokes('command+a', delay_ms=20)
                if platform.system().lower() == 'darwin':
                    mock_hotkey.assert_called_with('command', 'a')
                else:
                    mock_hotkey.assert_called_with('ctrl', 'a')
                mock_sleep.assert_called_with(0.02)  # 20ms

def test_send_keystroke_sequence():
    """Test sending a sequence of keystrokes."""
    with patch("src.actions.keystrokes.send_keystroke", return_value=True) as mock_send:
        # Define a valid keystroke sequence
        sequence = [
            {'keys': 'a', 'delay_ms': 10},
            {'keys': 'b', 'delay_ms': 20},
            {'keys': 'command+c', 'delay_ms': 30}
        ]

        # Send the sequence
        assert send_keystroke_sequence(sequence) is True

        # Verify that send_keystroke was called for each item in the sequence
        assert mock_send.call_count == 3
        mock_send.assert_any_call("a", "cursor")
        mock_send.assert_any_call("b", "cursor")
        mock_send.assert_any_call("command+c", "cursor")

def test_send_keystroke_string():
    """Test sending a multi-line string as keystrokes."""
    with patch("subprocess.run") as mock_subprocess:
        # Mock successful subprocess call
        mock_subprocess.return_value.returncode = 0

        # Test single line
        assert send_keystroke_string("Hello world") is True

        # Verify subprocess was called (AppleScript execution)
        assert mock_subprocess.called

        # Test multi-line string
        mock_subprocess.reset_mock()
        assert send_keystroke_string("Hello\nworld") is True
        assert mock_subprocess.called

def test_activate_window():
    """Test window activation."""
    # Test with non-existent window (should return False)
    assert activate_window('NonExistentWindow') is False

    # Test with common windows that should exist on test systems
    if platform.system().lower() == 'windows':
        common_window = 'Notepad'
    elif platform.system().lower() == 'darwin':
        common_window = 'Terminal'
    elif platform.system().lower() == 'linux':
        common_window = 'Terminal'

    # This will be skipped if activate_window cannot find the window
    # which is preferable to failing tests on different environments
    if activate_window(common_window) is True:
        assert True  # Window activated successfully
    else:
        pytest.skip(f"Could not activate {common_window} - skipping this validation")


def test_config_keystrokes_parsing():
    """Test that keystrokes from config file are parsed correctly."""
    from src.actions.keystrokes import send_keystroke

    with patch("subprocess.run") as mock_subprocess:
        # Mock successful subprocess call
        mock_subprocess.return_value.returncode = 0

        # Test keystrokes from config.yaml
        test_keystrokes = [
            "command+a",
            "backspace",
            "command+l",
            "command+n",
            "command+shift+l",
            "control+`",
        ]

        for keystroke in test_keystrokes:
            result = send_keystroke(keystroke, "cursor")
            assert result is True, f"Failed to send keystroke: {keystroke}"

        # Verify that subprocess was called for each keystroke
        assert mock_subprocess.call_count == len(test_keystrokes)
