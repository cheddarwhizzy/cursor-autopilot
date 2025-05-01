import os
import pytest
from unittest.mock import patch, MagicMock
import logging
from src.actions.keystrokes import map_key, send_keystrokes, send_keystroke_sequence, activate_window

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

def test_send_keystrokes():
    """Test sending keystrokes."""
    # Test single key
    assert send_keystrokes('a', delay_ms=0) is True
    
    # Test modifier key combination
    if platform.system().lower() == 'windows' or platform.system().lower() == 'linux':
        assert send_keystrokes('command+a', delay_ms=0) is True
    else:
        assert send_keystrokes('command+a', delay_ms=0) is True
    
    # Test invalid key (should return False)
    assert send_keystrokes('invalid_key', delay_ms=0) is False

def test_send_keystroke_sequence():
    """Test sending a sequence of keystrokes."""
    sequence = [
        {'keys': 'a', 'delay_ms': 0},
        {'keys': 'command+a', 'delay_ms': 0},
        {'keys': 'shift+enter', 'delay_ms': 0}
    ]
    assert send_keystroke_sequence(sequence) is True
    
    # Test with invalid key (should return False)
    invalid_sequence = [
        {'keys': 'a', 'delay_ms': 0},
        {'keys': 'invalid_key', 'delay_ms': 0},
        {'keys': 'b', 'delay_ms': 0}
    ]
    assert send_keystroke_sequence(invalid_sequence) is False

def test_activate_window():
    """Test window activation."""
    # Test with non-existent window (should return False)
    assert activate_window('NonExistentWindow') is False
    
    # Test with current window (should return True)
    if platform.system().lower() == 'windows':
        assert activate_window('Python') is True
    elif platform.system().lower() == 'darwin':
        assert activate_window('Terminal') is True
    elif platform.system().lower() == 'linux':
        assert activate_window('Terminal') is True 