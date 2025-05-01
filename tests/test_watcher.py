import os
import pytest
from unittest.mock import patch, MagicMock, call
import time
import hashlib
import yaml
import logging
from src.watcher import (
    load_gitignore_patterns,
    get_platform_config,
    check_vision_conditions,
    send_slack_message,
    hash_folder_state,
    run_watcher,
    load_config
)

# Configure logging
logger = logging.getLogger('watcher')

@pytest.fixture
def mock_config():
    return {
        "platform": ["cursor", "windsurf"],
        "platforms": {
            "cursor": {
                "project_path": "/test/cursor",
                "task_file_path": "tasks.md",
                "os_type": "osx",
                "keystrokes": [
                    {"keys": "command+k", "delay_ms": 100},
                    {"keys": "command+l", "delay_ms": 200}
                ],
                "options": {
                    "vision_conditions": [
                        {
                            "file_type": "*.py",
                            "action": "change",
                            "question": "Is this Python code?",
                            "success_keystrokes": [{"keys": "command+s"}],
                            "failure_keystrokes": [{"keys": "command+q"}]
                        }
                    ],
                    "send_inactivity_prompt": True,
                    "inactivity_prompt": "continue"
                }
            },
            "windsurf": {
                "project_path": "/test/windsurf",
                "task_file_path": "tasks.md",
                "os_type": "osx",
                "keystrokes": [
                    {"keys": "command+k", "delay_ms": 100},
                    {"keys": "command+l", "delay_ms": 200}
                ],
                "options": {
                    "vision_conditions": [
                        {
                            "file_type": "*.js",
                            "action": "change",
                            "question": "Is this JavaScript code?",
                            "success_keystrokes": [{"keys": "command+s"}],
                            "failure_keystrokes": [{"keys": "command+q"}]
                        }
                    ],
                    "send_inactivity_prompt": True,
                    "inactivity_prompt": "continue"
                }
            }
        },
        "inactivity_delay": 120,
        "poll_interval": 1,
        "openai": {
            "vision": {
                "enabled": True,
                "api_key": "test_key",
                "model": "gpt-4-vision-preview",
                "max_tokens": 100,
                "temperature": 0.7
            }
        },
        "slack": {
            "enabled": True,
            "bot_token": "test_token",
            "app_token": "test_token",
            "channels": [
                {"name": "automation", "id": "C123"}
            ]
        }
    }

@pytest.fixture
def mock_gitignore():
    return """
# Python
__pycache__/
*.py[cod]
*$py.class

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/

# Custom
*.tmp
*.log
test.txt
"""

@pytest.fixture(autouse=True)
def setup_environment(monkeypatch, mock_config, tmp_path):
    """Set up environment variables and global config for all tests."""
    # Create a temporary config file
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)
    
    # Patch paths and config
    monkeypatch.setattr('src.watcher.CONFIG_PATH', str(config_path))
    monkeypatch.setattr('src.watcher.CURRENT_OS', 'osx')
    
    # Load config
    load_config()

def test_load_gitignore_patterns(tmp_path, mock_gitignore):
    # Create a temporary .gitignore file
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(mock_gitignore)
    
    # Load patterns
    patterns = load_gitignore_patterns(str(gitignore_path))
    
    # Verify patterns
    assert "__pycache__" in patterns
    assert "node_modules" in patterns
    assert "*.tmp" in patterns
    assert "test.txt" in patterns

def test_load_gitignore_patterns_missing_file(tmp_path):
    # Test with nonexistent file
    patterns = load_gitignore_patterns(str(tmp_path / "nonexistent"))
    assert patterns == set()

@patch('src.watcher.CURRENT_OS', 'osx')
def test_get_platform_config_osx(mock_config):
    config = get_platform_config("cursor")
    assert config["os_type"] == "osx"
    assert config["keystrokes"][0]["keys"] == "command+k"

@patch('src.watcher.CURRENT_OS', 'windows')
def test_get_platform_config_windows(mock_config):
    config = get_platform_config("cursor")
    assert config["os_type"] == "osx"  # Original config
    assert config["keystrokes"][0]["keys"] == "ctrl+k"  # Converted for Windows

@patch('src.watcher.openai_client')
def test_check_vision_conditions_multi_platform(mock_openai, mock_config):
    # Setup mock response for Python file
    python_response = MagicMock()
    python_response.choices[0].message.content = "yes"
    
    # Setup mock response for JavaScript file
    js_response = MagicMock()
    js_response.choices[0].message.content = "yes"
    
    # Configure mock to return different responses based on file type
    def mock_create(**kwargs):
        file_path = kwargs['messages'][0]['content'][1]['image_url']['url']
        if file_path.endswith('.py'):
            return python_response
        elif file_path.endswith('.js'):
            return js_response
        return None
    
    mock_openai.chat.completions.create.side_effect = mock_create
    
    # Test Python file with Cursor platform
    result_py = check_vision_conditions("test.py", "change", "cursor")
    assert result_py is not None
    question_py, keystrokes_py = result_py
    assert question_py == "Is this Python code?"
    assert keystrokes_py[0]["keys"] == "command+s"
    
    # Test JavaScript file with Windsurf platform
    result_js = check_vision_conditions("test.js", "change", "windsurf")
    assert result_js is not None
    question_js, keystrokes_js = result_js
    assert question_js == "Is this JavaScript code?"
    assert keystrokes_js[0]["keys"] == "command+s"

@patch('src.watcher.openai_client')
def test_check_vision_conditions_multi_platform_failure(mock_openai, mock_config):
    # Setup mock response for wrong file types
    wrong_type_response = MagicMock()
    wrong_type_response.choices[0].message.content = "no"
    mock_openai.chat.completions.create.return_value = wrong_type_response
    
    # Test JavaScript file with Cursor platform (should use Python condition)
    result_js_cursor = check_vision_conditions("test.js", "change", "cursor")
    assert result_js_cursor is not None
    question_js_cursor, keystrokes_js_cursor = result_js_cursor
    assert question_js_cursor == "Is this Python code?"
    assert keystrokes_js_cursor[0]["keys"] == "command+q"
    
    # Test Python file with Windsurf platform (should use JavaScript condition)
    result_py_windsurf = check_vision_conditions("test.py", "change", "windsurf")
    assert result_py_windsurf is not None
    question_py_windsurf, keystrokes_py_windsurf = result_py_windsurf
    assert question_py_windsurf == "Is this JavaScript code?"
    assert keystrokes_py_windsurf[0]["keys"] == "command+q"

@patch('src.watcher.openai_client')
def test_check_vision_conditions_api_error(mock_openai, mock_config):
    # Setup mock to simulate API error
    mock_openai.chat.completions.create.side_effect = Exception("API Error")
    
    # Test with both platforms
    result_cursor = check_vision_conditions("test.py", "change", "cursor")
    assert result_cursor is None
    
    result_windsurf = check_vision_conditions("test.js", "change", "windsurf")
    assert result_windsurf is None

@patch('src.watcher.requests.post')
def test_send_slack_message_success(mock_post, mock_config):
    # Setup mock response
    mock_post.return_value.ok = True
    
    # Send message
    send_slack_message("Test message")
    
    # Verify request
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[1]["json"]["channel"] == "C123"
    assert args[1]["json"]["text"] == "Test message"
    assert args[1]["headers"]["Authorization"] == "Bearer test_token"

@patch('src.watcher.requests.post')
def test_send_slack_message_failure(mock_post, mock_config):
    # Setup mock response
    mock_post.return_value.ok = False
    mock_post.return_value.text = "Error"
    
    # Send message
    send_slack_message("Test message")
    
    # Verify request was made but error was logged
    mock_post.assert_called_once()

def test_hash_folder_state(tmp_path):
    # Create test files
    (tmp_path / "test1.txt").write_text("test1")
    (tmp_path / "test2.txt").write_text("test2")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules/test.txt").write_text("ignore")
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(tmp_path)), \
         patch('src.watcher.EXCLUDE_DIRS', {"node_modules"}), \
         patch('src.watcher.GITIGNORE_PATTERNS', {"config.yaml"}):
        
        # Get initial state
        hash1, changed1, total1 = hash_folder_state()
        assert total1 == 2  # Only test1.txt and test2.txt
        assert len(changed1) == 2  # Both files are new
        
        # Modify a file
        time.sleep(0.1)  # Ensure mtime changes
        (tmp_path / "test1.txt").write_text("modified")
        
        # Get new state
        hash2, changed2, total2 = hash_folder_state()
        assert total2 == 2
        assert len(changed2) == 1  # Only test1.txt changed
        assert "test1.txt" in changed2
        assert hash1 != hash2  # Hash should be different

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.return_value = ("hash", ["test.py", "test.js"], 2)
    
    # Mock OpenAI API responses
    mock_openai.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="yes"))]
    )
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Create test files
    (cursor_path / "test.py").write_text("print('Hello')")
    (windsurf_path / "test.js").write_text("console.log('Hello')")
    
    # Create task file
    task_file = tmp_path / "tasks.md"
    task_file.write_text("# Tasks")
    
    # Create initial prompt file
    initial_prompt_file = tmp_path / "initial_prompt.txt"
    initial_prompt_file.write_text("Initial prompt")
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.TASK_FILE_PATH', "tasks.md"), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai):  # Ensure OpenAI client is properly mocked
        
        # Create config file
        with open(tmp_path / "config.yaml", "w") as f:
            yaml.dump(mock_config, f)
        
        # Run watcher in a separate thread
        import threading
        watcher_thread = threading.Thread(target=run_watcher)
        watcher_thread.daemon = True
        watcher_thread.start()
        
        # Wait for prompts to be sent
        time.sleep(2)
        
        # Verify prompts were sent for each platform
        assert mock_send.call_count >= 2  # At least one call per platform
        calls = mock_send.call_args_list
        platforms = set()
        for call in calls:
            args, kwargs = call
            platforms.add(kwargs.get("platform"))
        assert "cursor" in platforms
        assert "windsurf" in platforms
        
        # Verify OpenAI API was called for each file
        assert mock_openai.chat.completions.create.call_count >= 2
        api_calls = mock_openai.chat.completions.create.call_args_list
        file_types = set()
        for call in api_calls:
            args, kwargs = call
            messages = kwargs["messages"]
            for message in messages:
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and "image_url" in item:
                                file_url = item["image_url"]["url"]
                                if "test.py" in file_url:
                                    file_types.add("python")
                                elif "test.js" in file_url:
                                    file_types.add("javascript")
        assert "python" in file_types
        assert "javascript" in file_types

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher_multi_platform(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.side_effect = [
        ("hash1", ["test.py", "test.js"], 2),  # First call
        ("hash2", ["test.py"], 1),             # Second call
        ("hash3", ["test.js"], 1),             # Third call
        KeyboardInterrupt                       # Fourth call to stop the loop
    ]
    
    # Mock OpenAI API responses
    def mock_create(**kwargs):
        response = MagicMock()
        file_path = kwargs['messages'][0]['content'][1]['image_url']['url']
        response.choices[0].message.content = "yes" if file_path.endswith(('.py', '.js')) else "no"
        return response
    
    mock_openai.chat.completions.create.side_effect = mock_create
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Create test files
    (cursor_path / "test.py").write_text("print('Hello')")
    (windsurf_path / "test.js").write_text("console.log('Hello')")
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai):
        
        # Create config file
        with open(tmp_path / "config.yaml", "w") as f:
            yaml.dump(mock_config, f)
        
        # Run watcher
        run_watcher()
        
        # Verify vision conditions were checked for both platforms
        vision_calls = mock_openai.chat.completions.create.call_args_list
        assert len(vision_calls) >= 2
        
        # Verify prompts were sent for both platforms
        send_calls = mock_send.call_args_list
        cursor_calls = [call for call in send_calls if call[1].get('platform') == 'cursor']
        windsurf_calls = [call for call in send_calls if call[1].get('platform') == 'windsurf']
        assert len(cursor_calls) > 0
        assert len(windsurf_calls) > 0

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher_multi_platform_inactivity(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.side_effect = [
        ("hash1", [], 2),  # No changes
        ("hash1", [], 2),  # No changes
        KeyboardInterrupt  # Stop the loop
    ]
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai):
        
        # Create config file
        with open(tmp_path / "config.yaml", "w") as f:
            yaml.dump(mock_config, f)
        
        # Run watcher
        run_watcher()
        
        # Verify inactivity prompts were sent for both platforms
        send_calls = mock_send.call_args_list
        cursor_inactivity_calls = [
            call for call in send_calls 
            if call[1].get('platform') == 'cursor' and 
               mock_config["platforms"]["cursor"]["options"]["inactivity_prompt"] in str(call)
        ]
        windsurf_inactivity_calls = [
            call for call in send_calls 
            if call[1].get('platform') == 'windsurf' and 
               mock_config["platforms"]["windsurf"]["options"]["inactivity_prompt"] in str(call)
        ]
        assert len(cursor_inactivity_calls) > 0
        assert len(windsurf_inactivity_calls) > 0 

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher_multi_platform_error_handling(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.side_effect = [
        ("hash1", ["test.py", "test.js"], 2),  # First call
        Exception("File system error"),         # Second call
        ("hash2", ["test.py"], 1),             # Third call
        KeyboardInterrupt                      # Fourth call to stop the loop
    ]
    
    # Mock OpenAI API responses with error
    def mock_create(**kwargs):
        if "test.py" in str(kwargs):
            raise Exception("OpenAI API error")
        response = MagicMock()
        response.choices[0].message.content = "yes"
        return response
    
    mock_openai.chat.completions.create.side_effect = mock_create
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Create test files
    (cursor_path / "test.py").write_text("print('Hello')")
    (windsurf_path / "test.js").write_text("console.log('Hello')")
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai), \
         patch('src.watcher.logger') as mock_logger:
        
        # Create config file
        with open(tmp_path / "config.yaml", "w") as f:
            yaml.dump(mock_config, f)
        
        # Run watcher
        run_watcher()
        
        # Verify error logging
        error_logs = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("File system error" in str(log) for log in error_logs)
        assert any("OpenAI API error" in str(log) for log in error_logs)
        
        # Verify watcher continued running despite errors
        assert mock_hash.call_count >= 3
        assert mock_send.call_count > 0

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher_multi_platform_edge_cases(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.side_effect = [
        ("hash1", [], 0),                      # No files
        ("hash2", ["test.py", "test.js"], 2),  # Both platforms
        ("hash3", ["test.py"], 1),             # Only Cursor
        ("hash4", ["test.js"], 1),             # Only Windsurf
        KeyboardInterrupt                      # Stop the loop
    ]
    
    # Mock OpenAI API responses
    def mock_create(**kwargs):
        response = MagicMock()
        file_path = kwargs['messages'][0]['content'][1]['image_url']['url']
        response.choices[0].message.content = "yes" if file_path.endswith(('.py', '.js')) else "no"
        return response
    
    mock_openai.chat.completions.create.side_effect = mock_create
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Create test files
    (cursor_path / "test.py").write_text("print('Hello')")
    (windsurf_path / "test.js").write_text("console.log('Hello')")
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai):
        
        # Create config file
        with open(tmp_path / "config.yaml", "w") as f:
            yaml.dump(mock_config, f)
        
        # Run watcher
        run_watcher()
        
        # Verify handling of empty file list
        assert mock_send.call_count > 0
        
        # Verify handling of single platform changes
        send_calls = mock_send.call_args_list
        cursor_calls = [call for call in send_calls if call[1].get('platform') == 'cursor']
        windsurf_calls = [call for call in send_calls if call[1].get('platform') == 'windsurf']
        assert len(cursor_calls) > 0
        assert len(windsurf_calls) > 0

@patch('src.watcher.get_mode')
@patch('src.watcher.send_prompt')
@patch('src.watcher.hash_folder_state')
@patch('src.watcher.openai_client')
def test_run_watcher_multi_platform_config_changes(mock_openai, mock_hash, mock_send, mock_mode, tmp_path, mock_config):
    # Setup mocks
    mock_mode.return_value = "auto"
    mock_hash.side_effect = [
        ("hash1", ["test.py", "test.js"], 2),  # First call
        ("hash2", ["test.py"], 1),             # Second call
        ("hash3", ["test.js"], 1),             # Third call
        KeyboardInterrupt                      # Fourth call to stop the loop
    ]
    
    # Mock OpenAI API responses
    def mock_create(**kwargs):
        response = MagicMock()
        file_path = kwargs['messages'][0]['content'][1]['image_url']['url']
        response.choices[0].message.content = "yes" if file_path.endswith(('.py', '.js')) else "no"
        return response
    
    mock_openai.chat.completions.create.side_effect = mock_create
    
    # Create test directories
    cursor_path = tmp_path / "cursor"
    windsurf_path = tmp_path / "windsurf"
    cursor_path.mkdir()
    windsurf_path.mkdir()
    
    # Create test files
    (cursor_path / "test.py").write_text("print('Hello')")
    (windsurf_path / "test.js").write_text("console.log('Hello')")
    
    # Update mock config with correct paths
    mock_config["platforms"]["cursor"]["project_path"] = str(cursor_path)
    mock_config["platforms"]["windsurf"]["project_path"] = str(windsurf_path)
    
    # Set up test environment
    with patch('src.watcher.WATCH_PATH', str(cursor_path)), \
         patch('src.watcher.inactivity_delay_val', 1), \
         patch('src.watcher.last_activity', time.time() - 2), \
         patch('src.watcher.last_prompt_time', 0.0), \
         patch('src.watcher.inactivity_timer', 2.0), \
         patch('src.watcher.CONFIG_PATH', str(tmp_path / "config.yaml")), \
         patch('src.watcher.os.path.exists', return_value=True), \
         patch('src.watcher.openai_client', mock_openai), \
         patch('src.watcher.load_config') as mock_load_config:
        
        # Create config file
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(mock_config, f)
        
        # Simulate config changes during runtime
        def mock_load():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        
        mock_load_config.side_effect = [
            mock_load(),  # Initial load
            mock_load(),  # First check
            mock_load(),  # Second check
            mock_load()   # Third check
        ]
        
        # Run watcher
        run_watcher()
        
        # Verify config was reloaded
        assert mock_load_config.call_count >= 4
        
        # Verify watcher continued running with updated config
        assert mock_hash.call_count >= 3
        assert mock_send.call_count > 0 