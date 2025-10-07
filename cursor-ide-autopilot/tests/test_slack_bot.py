import os
import pytest
from unittest.mock import patch, MagicMock
import logging
from flask import Flask
from src.slack_bot import app, slack_command

# Configure logging
logger = logging.getLogger('slack_bot')

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_slack_command_code(client):
    # Test setting mode to code
    response = client.post('/cursor', data={'text': 'code', 'user_name': 'testuser'})
    assert response.status_code == 200
    assert b"Mode set to CODE" in response.data
    assert b"testuser" in response.data

def test_slack_command_auto(client):
    # Test setting mode to auto
    response = client.post('/cursor', data={'text': 'auto'})
    assert response.status_code == 200
    assert b"Mode set to AUTO" in response.data

@patch('src.slack_bot.send_prompt')
def test_slack_command_send(mock_send_prompt, client):
    # Test sending a prompt
    test_prompt = "test prompt"
    response = client.post('/cursor', data={'text': f'send {test_prompt}'})
    
    assert response.status_code == 200
    assert b"Sent to Cursor: test prompt" in response.data
    mock_send_prompt.assert_called_once_with(test_prompt)

@patch('src.slack_bot.capture_chat_screenshot')
def test_slack_command_screenshot(mock_capture_screenshot, client):
    # Test taking a screenshot
    mock_capture_screenshot.return_value = "/tmp/screenshot.png"
    response = client.post('/cursor', data={'text': 'screenshot'})
    
    assert response.status_code == 200
    assert b"Screenshot saved: /tmp/screenshot.png" in response.data
    mock_capture_screenshot.assert_called_once()

@patch('src.slack_bot.get_mode')
def test_slack_command_status(mock_get_mode, client):
    # Test getting status
    mock_get_mode.return_value = "code"
    response = client.post('/cursor', data={'text': 'status'})
    
    assert response.status_code == 200
    assert b"Mode: code" in response.data
    mock_get_mode.assert_called_once()

def test_slack_command_unknown(client):
    # Test unknown command
    response = client.post('/cursor', data={'text': 'unknown_command'})
    assert response.status_code == 200
    assert b"Unknown command." in response.data

def test_slack_command_empty_text(client):
    # Test empty text
    response = client.post('/cursor', data={'text': ''})
    assert response.status_code == 200
    assert b"Unknown command." in response.data

def test_slack_command_whitespace_text(client):
    # Test whitespace text
    response = client.post('/cursor', data={'text': '   '})
    assert response.status_code == 200
    assert b"Unknown command." in response.data

def test_slack_command_missing_text(client):
    # Test missing text parameter
    response = client.post('/cursor', data={})
    assert response.status_code == 200
    assert b"Unknown command." in response.data

@patch('src.slack_bot.send_prompt')
def test_slack_command_send_empty(mock_send_prompt, client):
    # Test sending empty prompt
    response = client.post('/cursor', data={'text': 'send'})
    
    assert response.status_code == 200
    assert b"Sent to Cursor: " in response.data
    mock_send_prompt.assert_called_once_with("")

@patch('src.slack_bot.send_prompt')
def test_slack_command_send_whitespace(mock_send_prompt, client):
    # Test sending whitespace prompt
    response = client.post('/cursor', data={'text': 'send    '})
    
    assert response.status_code == 200
    assert b"Sent to Cursor: " in response.data
    mock_send_prompt.assert_called_once_with("")

@patch('src.slack_bot.capture_chat_screenshot')
def test_slack_command_screenshot_error(mock_capture_screenshot, client):
    # Test screenshot error
    mock_capture_screenshot.side_effect = Exception("Screenshot error")
    response = client.post('/cursor', data={'text': 'screenshot'})
    
    assert response.status_code == 200
    assert b"Error taking screenshot: Screenshot error" in response.data
    mock_capture_screenshot.assert_called_once()

@patch('src.slack_bot.send_prompt')
def test_slack_command_send_error(mock_send_prompt, client):
    # Test send error
    mock_send_prompt.side_effect = Exception("Send error")
    response = client.post('/cursor', data={'text': 'send test'})
    
    assert response.status_code == 200
    assert b"Error sending prompt: Send error" in response.data
    mock_send_prompt.assert_called_once_with("test") 