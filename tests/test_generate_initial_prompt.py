import os
import pytest
from unittest.mock import patch, MagicMock
import logging
import openai
from src.generate_initial_prompt import (
    generate_prompt,
    get_config,
    read_prompt_from_file,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_CONTINUATION_PROMPT,
    INITIAL_PROMPT_SENT_PATH,
    INITIAL_PROMPT_PATH
)

# Configure logging
logger = logging.getLogger('generate_initial_prompt')

@pytest.fixture
def mock_config():
    return {
        "platform": "cursor",
        "use_vision_api": True
    }

@pytest.fixture
def mock_custom_prompts(tmp_path):
    initial_prompt_path = tmp_path / "custom_initial_prompt.txt"
    continuation_prompt_path = tmp_path / "custom_continuation_prompt.txt"
    
    initial_prompt_path.write_text("Custom initial prompt {task_file_path} {additional_context_path}")
    continuation_prompt_path.write_text("Custom continuation prompt {task_file_path} {additional_context_path}")
    
    return {
        "initial_prompt_file_path": str(initial_prompt_path),
        "continuation_prompt_file_path": str(continuation_prompt_path)
    }

@pytest.fixture
def mock_initial_prompt():
    return "This is a test initial prompt"

def test_get_config(tmp_path):
    # Create a temporary config file
    config_path = tmp_path / "config.yaml"
    config_content = """
    platform: cursor
    use_vision_api: true
    """
    config_path.write_text(config_content)
    
    with patch('src.generate_initial_prompt.os.path.join', return_value=str(config_path)):
        config = get_config()
        assert config["platform"] == "cursor"
        assert config["use_vision_api"] is True

def test_get_config_missing_file():
    with patch('src.generate_initial_prompt.os.path.join', return_value="/nonexistent/config.yaml"):
        config = get_config()
        assert config == {}

def test_read_prompt_from_file(tmp_path):
    # Create a temporary prompt file
    prompt_path = tmp_path / "initial_prompt.txt"
    prompt_content = "This is a test prompt"
    prompt_path.write_text(prompt_content)
    
    prompt = read_prompt_from_file(str(prompt_path))
    assert prompt == prompt_content

def test_read_prompt_from_missing_file():
    prompt = read_prompt_from_file("/nonexistent/initial_prompt.txt")
    assert prompt is None

def test_read_prompt_from_file_nonexistent():
    prompt = read_prompt_from_file("/nonexistent/path")
    assert prompt is None

def test_read_prompt_from_file_none():
    prompt = read_prompt_from_file(None)
    assert prompt is None

@patch('src.generate_initial_prompt.get_config')
@patch('src.generate_initial_prompt.read_prompt_from_file')
@patch('openai.ChatCompletion.create')
def test_generate_prompt_new_chat(
    mock_openai_create,
    mock_read_prompt,
    mock_get_config,
    mock_config,
    mock_initial_prompt,
    tmp_path
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_read_prompt.return_value = None
    mock_openai_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=mock_initial_prompt))]
    )
    
    # Create temporary paths
    prompt_path = tmp_path / "initial_prompt.txt"
    marker_path = tmp_path / ".initial_prompt_sent"
    
    # Patch module-level paths
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(prompt_path)), \
         patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(marker_path)):
        
        # Call the function
        generate_prompt()
        
        # Verify files were created
        assert os.path.exists(prompt_path)
        assert os.path.exists(marker_path)
        
        # Verify prompt content
        with open(prompt_path, "r") as f:
            assert "You are working in a pre-existing application" in f.read()

@patch('src.generate_initial_prompt.get_config')
@patch('src.generate_initial_prompt.read_prompt_from_file')
@patch('openai.ChatCompletion.create')
def test_generate_prompt_existing_chat(
    mock_openai_create,
    mock_read_prompt,
    mock_get_config,
    mock_config,
    mock_initial_prompt,
    tmp_path
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_read_prompt.return_value = None  # No custom continuation prompt
    
    # Create temporary paths
    prompt_path = tmp_path / "initial_prompt.txt"
    marker_path = tmp_path / ".initial_prompt_sent"
    
    # Create marker file to simulate existing chat
    marker_path.touch()
    
    # Patch module-level paths
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(prompt_path)), \
         patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(marker_path)):
        
        # Call the function
        generate_prompt()
        
        # Verify files
        assert os.path.exists(prompt_path)
        assert os.path.exists(marker_path)  # Marker file should still exist
        
        # Verify prompt content
        with open(prompt_path, "r") as f:
            content = f.read()
            assert "Continue working on the tasks" in content
            assert "tasks.md" in content  # Task file path should be formatted
            assert "context.md" in content  # Additional context path should be formatted

@patch('src.generate_initial_prompt.get_config')
@patch('src.generate_initial_prompt.read_prompt_from_file')
@patch('openai.ChatCompletion.create')
def test_generate_prompt_api_error(
    mock_openai_create,
    mock_read_prompt,
    mock_get_config,
    mock_config,
    tmp_path
):
    # Setup mocks
    mock_get_config.return_value = mock_config
    mock_read_prompt.return_value = None
    mock_openai_create.side_effect = Exception("API Error")
    
    # Create temporary paths
    prompt_path = tmp_path / "initial_prompt.txt"
    marker_path = tmp_path / ".initial_prompt_sent"
    
    # Patch module-level paths
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(prompt_path)), \
         patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(marker_path)):
        
        # Call the function
        generate_prompt()
        
        # Verify files were created (even with API error)
        assert os.path.exists(prompt_path)
        assert os.path.exists(marker_path)

@patch('src.generate_initial_prompt.get_config')
def test_generate_prompt_initial(mock_get_config, mock_config, tmp_path):
    # Setup mocks
    mock_get_config.return_value = mock_config
    
    # Ensure marker file doesn't exist
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(tmp_path / ".initial_prompt_sent")):
        with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(tmp_path / "initial_prompt.txt")):
            # Generate prompt
            prompt = generate_prompt()
            
            # Verify prompt content
            assert "tasks.md" in prompt
            assert "context.md" in prompt
            assert DEFAULT_INITIAL_PROMPT.format(task_file_path="tasks.md", additional_context_path="context.md") == prompt
            
            # Verify files were created
            assert os.path.exists(str(tmp_path / ".initial_prompt_sent"))
            assert os.path.exists(str(tmp_path / "initial_prompt.txt"))

@patch('src.generate_initial_prompt.get_config')
def test_generate_prompt_continuation(mock_get_config, mock_config, tmp_path):
    # Setup mocks
    mock_get_config.return_value = mock_config
    
    # Create marker file to simulate existing chat
    marker_path = tmp_path / ".initial_prompt_sent"
    marker_path.write_text("")
    
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(marker_path)):
        with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(tmp_path / "initial_prompt.txt")):
            # Generate prompt
            prompt = generate_prompt()
            
            # Verify prompt content
            assert "tasks.md" in prompt
            assert "context.md" in prompt
            assert DEFAULT_CONTINUATION_PROMPT.format(task_file_path="tasks.md", additional_context_path="context.md") == prompt
            
            # Verify only prompt file was created (marker file already exists)
            assert os.path.exists(str(tmp_path / "initial_prompt.txt"))

@patch('src.generate_initial_prompt.get_config')
def test_generate_prompt_custom_initial(mock_get_config, mock_config, mock_custom_prompts, tmp_path):
    # Setup mocks
    mock_get_config.return_value = {**mock_config, **mock_custom_prompts}
    
    # Ensure marker file doesn't exist
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(tmp_path / ".initial_prompt_sent")):
        with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(tmp_path / "initial_prompt.txt")):
            # Generate prompt
            prompt = generate_prompt()
            
            # Verify prompt content
            assert "Custom initial prompt" in prompt
            assert "tasks.md" in prompt
            assert "context.md" in prompt
            
            # Verify files were created
            assert os.path.exists(str(tmp_path / ".initial_prompt_sent"))
            assert os.path.exists(str(tmp_path / "initial_prompt.txt"))

@patch('src.generate_initial_prompt.get_config')
def test_generate_prompt_custom_continuation(mock_get_config, mock_config, mock_custom_prompts, tmp_path):
    # Setup mocks
    mock_get_config.return_value = {**mock_config, **mock_custom_prompts}
    
    # Create marker file to simulate existing chat
    marker_path = tmp_path / ".initial_prompt_sent"
    marker_path.write_text("")
    
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(marker_path)):
        with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(tmp_path / "initial_prompt.txt")):
            # Generate prompt
            prompt = generate_prompt()
            
            # Verify prompt content
            assert "Custom continuation prompt" in prompt
            assert "tasks.md" in prompt
            assert "context.md" in prompt
            
            # Verify only prompt file was created (marker file already exists)
            assert os.path.exists(str(tmp_path / "initial_prompt.txt"))

@patch('src.generate_initial_prompt.get_config')
def test_generate_prompt_custom_file_error(mock_get_config, mock_config, tmp_path):
    # Setup mocks with nonexistent custom prompt files
    mock_get_config.return_value = {
        **mock_config,
        "initial_prompt_file_path": "/nonexistent/initial.txt",
        "continuation_prompt_file_path": "/nonexistent/continuation.txt"
    }
    
    # Ensure marker file doesn't exist
    with patch('src.generate_initial_prompt.INITIAL_PROMPT_SENT_PATH', str(tmp_path / ".initial_prompt_sent")):
        with patch('src.generate_initial_prompt.INITIAL_PROMPT_PATH', str(tmp_path / "initial_prompt.txt")):
            # Generate prompt
            prompt = generate_prompt()
            
            # Verify default prompt was used
            assert DEFAULT_INITIAL_PROMPT.format(task_file_path="tasks.md", additional_context_path="context.md") == prompt
            
            # Verify files were created
            assert os.path.exists(str(tmp_path / ".initial_prompt_sent"))
            assert os.path.exists(str(tmp_path / "initial_prompt.txt")) 