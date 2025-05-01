import os
import pytest
from unittest.mock import patch, MagicMock, call
import logging
import threading
import subprocess
import time
import signal
from src.run_both import run_flask, run_watcher, stream_output, get_config, main

# Configure logging
logger = logging.getLogger('run_both')

@pytest.fixture
def mock_config():
    return {
        "platform": "cursor",
        "use_vision_api": True
    }

@pytest.fixture
def mock_process():
    process = MagicMock()
    process.stdout.readline.side_effect = [
        b"Test output line 1\n",
        b"Test output line 2\n",
        b""  # Empty line to simulate end of output
    ]
    return process

def test_get_config(tmp_path):
    # Create a temporary config file
    config_path = tmp_path / "config.yaml"
    config_content = """
    platform: cursor
    use_vision_api: true
    """
    config_path.write_text(config_content)
    
    with patch('src.run_both.os.path.join', return_value=str(config_path)):
        config = get_config()
        assert config["platform"] == "cursor"
        assert config["use_vision_api"] is True

def test_get_config_missing_file():
    with patch('src.run_both.os.path.join', return_value="/nonexistent/config.yaml"):
        config = get_config()
        assert config == {}

@patch('src.run_both.logger')
def test_stream_output(mock_logger):
    # Create a mock process with predefined output
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [
        b"First line\n",
        b"Second line\n",
        b"",  # Empty line to simulate end of output
    ]
    
    # Call stream_output
    stream_output(mock_process, "TEST")
    
    # Verify logging calls
    mock_logger.info.assert_has_calls([
        call("TEST | First line"),
        call("TEST | Second line")
    ])

@patch('src.run_both.subprocess.Popen')
@patch('src.run_both.stream_output')
def test_run_flask(mock_stream_output, mock_popen):
    # Setup mock process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    # Call run_flask
    run_flask()
    
    # Verify Popen was called with correct arguments
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0] == ["flask", "run", "--port=5005"]
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.STDOUT
    assert kwargs["text"] is False
    assert kwargs["env"]["FLASK_APP"] == "slack_bot.py"
    
    # Verify stream_output was called
    mock_stream_output.assert_called_once_with(mock_process, "FLASK")

@patch('src.run_both.subprocess.Popen')
@patch('src.run_both.stream_output')
def test_run_watcher(mock_stream_output, mock_popen):
    # Setup mock process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    # Call run_watcher
    run_watcher()
    
    # Verify Popen was called with correct arguments
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0] == ["python3", "watcher.py"]
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.STDOUT
    assert kwargs["text"] is False
    
    # Verify stream_output was called
    mock_stream_output.assert_called_once_with(mock_process, "WATCH")

@patch('src.run_both.threading.Thread')
@patch('src.run_both.logger')
def test_main_normal_execution(mock_logger, mock_thread):
    # Setup mock threads
    mock_flask_thread = MagicMock()
    mock_watcher_thread = MagicMock()
    mock_thread.side_effect = [mock_flask_thread, mock_watcher_thread]
    
    # Setup join to raise KeyboardInterrupt after first call
    mock_flask_thread.join.side_effect = KeyboardInterrupt()
    
    # Call main and expect SystemExit
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    # Verify exit code is 0 (clean shutdown)
    assert exc_info.value.code == 0
    
    # Verify threads were created and started
    assert mock_thread.call_count == 2
    assert mock_flask_thread.daemon is True
    assert mock_watcher_thread.daemon is True
    mock_flask_thread.start.assert_called_once()
    mock_watcher_thread.start.assert_called_once()
    
    # Verify logging
    mock_logger.info.assert_has_calls([
        call("Starting both processes..."),
        call("Shutting down...")
    ])

@patch('src.run_both.threading.Thread')
@patch('src.run_both.logger')
def test_main_thread_exception(mock_logger, mock_thread):
    # Setup mock threads
    mock_flask_thread = MagicMock()
    mock_watcher_thread = MagicMock()
    mock_thread.side_effect = [mock_flask_thread, mock_watcher_thread]
    
    # Setup join to raise an exception
    mock_flask_thread.join.side_effect = Exception("Thread error")
    
    # Call main and expect exception to be raised
    with pytest.raises(Exception, match="Thread error"):
        main()
    
    # Verify threads were created and started
    assert mock_thread.call_count == 2
    assert mock_flask_thread.daemon is True
    assert mock_watcher_thread.daemon is True
    mock_flask_thread.start.assert_called_once()
    mock_watcher_thread.start.assert_called_once()
    
    # Verify logging
    mock_logger.info.assert_called_once_with("Starting both processes...")

@patch('src.run_both.subprocess.Popen')
def test_run_flask_process_error(mock_popen):
    # Setup mock to raise error
    mock_popen.side_effect = subprocess.SubprocessError("Process error")
    
    # Run the function and expect exception
    with pytest.raises(subprocess.SubprocessError) as exc_info:
        run_flask()
    
    # Verify error message
    assert str(exc_info.value) == "Process error"

@patch('src.run_both.subprocess.Popen')
def test_run_watcher_process_error(mock_popen):
    # Setup mock to raise error
    mock_popen.side_effect = subprocess.SubprocessError("Process error")
    
    # Run the function and expect exception
    with pytest.raises(subprocess.SubprocessError) as exc_info:
        run_watcher()
    
    # Verify error message
    assert str(exc_info.value) == "Process error" 