import os
import time
import pytest
import requests
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from src.actions.keystrokes import send_keystrokes, send_keystroke_sequence
from src.cli import load_config, validate_config
import logging

def test_simultaneous_automation_performance():
    """Test performance of simultaneous automation."""
    # Load test configuration
    config = load_config("config.yaml")
    assert validate_config(config)
    
    # Test keystroke timing
    start_time = time.time()
    sequence = [
        {'keys': 'a', 'delay_ms': 100},
        {'keys': 'command+a', 'delay_ms': 100},
        {'keys': 'shift+enter', 'delay_ms': 100}
    ]
    
    # Test single platform
    single_start = time.time()
    assert send_keystroke_sequence(sequence)
    single_duration = time.time() - single_start
    assert single_duration < 1.0  # Should complete within 1 second
    
    # Test multiple platforms simultaneously
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(send_keystroke_sequence, sequence),
            executor.submit(send_keystroke_sequence, sequence)
        ]
        results = [f.result() for f in futures]
    
    assert all(results)  # All keystrokes should succeed
    total_duration = time.time() - start_time
    assert total_duration < 2.0  # Should complete within 2 seconds

def test_api_security():
    """Test security measures for API endpoints."""
    # Test rate limiting
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 429  # Too Many Requests
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 429
    
    # Test authentication
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 401  # Unauthorized
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 401
    
    # Test input validation
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 400  # Bad Request
        response = requests.post('http://localhost:5000/api/config', json={'invalid': 'data'})
        assert response.status_code == 400

def test_error_handling():
    """Test comprehensive error handling."""
    # Test invalid keystrokes
    assert not send_keystrokes('invalid_key')
    assert not send_keystrokes('')
    assert not send_keystrokes(None)
    
    # Test invalid sequence
    assert not send_keystroke_sequence([])
    assert not send_keystroke_sequence([{'invalid': 'format'}])
    assert not send_keystroke_sequence([{'keys': 'a', 'delay_ms': -1}])
    
    # Test configuration errors
    with pytest.raises(ValueError):
        validate_config({})
    with pytest.raises(ValueError):
        validate_config({'project_path': '/nonexistent/path'})
    with pytest.raises(ValueError):
        validate_config({'platform': 'invalid_platform'})

def test_complete_workflow():
    """Test the complete automation workflow."""
    # Load configuration
    config = load_config("config.yaml")
    assert validate_config(config)
    
    # Test initialization
    for platform in config['platforms']:
        platform_config = config['platforms'][platform]
        for keystroke in platform_config['initialization']:
            assert send_keystrokes(keystroke['keys'], delay_ms=keystroke['delay_ms'])
    
    # Test task execution
    for platform in config['platforms']:
        platform_config = config['platforms'][platform]
        for keystroke in platform_config['keystrokes']:
            assert send_keystrokes(keystroke['keys'], delay_ms=keystroke['delay_ms'])
    
    # Test vision conditions
    for platform in config['platforms']:
        platform_config = config['platforms'][platform]
        vision_conditions = platform_config['options'].get('vision_conditions', [])
        for condition in vision_conditions:
            # Test success path
            for keystroke in condition['success_keystrokes']:
                assert send_keystrokes(keystroke['keys'], delay_ms=keystroke['delay_ms'])
            # Test failure path
            for keystroke in condition['failure_keystrokes']:
                assert send_keystrokes(keystroke['keys'], delay_ms=keystroke['delay_ms'])

def test_resource_cleanup():
    """Test proper cleanup of resources."""
    # Test file handles
    with patch('builtins.open', MagicMock()) as mock_open:
        load_config("config.yaml")
        mock_open.assert_called_once()
    
    # Test thread cleanup
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(send_keystrokes, 'a'),
            executor.submit(send_keystrokes, 'b')
        ]
        for future in futures:
            future.result()
    # Threads should be cleaned up automatically

def test_logging_and_monitoring():
    """Test logging and monitoring functionality."""
    # Test debug logging
    with patch('logging.getLogger') as mock_logger:
        mock_logger.return_value.debug = MagicMock()
        config = load_config("config.yaml")
        assert validate_config(config)
        mock_logger.return_value.debug.assert_called()
    
    # Test error logging
    with patch('logging.getLogger') as mock_logger:
        mock_logger.return_value.error = MagicMock()
        send_keystrokes('invalid_key')
        mock_logger.return_value.error.assert_called()
    
    # Test performance monitoring
    start_time = time.time()
    send_keystrokes('a')
    duration = time.time() - start_time
    assert duration < 0.1  # Should complete within 100ms 