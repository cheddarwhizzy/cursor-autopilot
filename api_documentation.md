# API Documentation

## Overview
This document provides comprehensive documentation for the Flask API endpoints, including request/response formats, examples, and test cases.

## Base URL
```
http://localhost:5000/api
```

## Authentication
All API endpoints require an API key to be included in the request header:
```
Authorization: Bearer <api_key>
```

## API Key Management

### Generating API Keys
API keys can be generated through the following methods:

1. **Command Line**
```bash
# Generate a new API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Python Script**
```python
import secrets
import hashlib

def generate_api_key():
    # Generate a random token
    token = secrets.token_urlsafe(32)
    # Create a hash of the token for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

# Example usage
api_key, api_key_hash = generate_api_key()
print(f"API Key: {api_key}")
print(f"Store this hash in your database: {api_key_hash}")
```

3. **Environment Variable**
```bash
# Set API key in environment
export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Storing API Keys
1. **Environment Variables**
```bash
# .env file
API_KEY=your_generated_api_key
```

2. **Configuration File**
```yaml
# config.yaml
api:
  keys:
    - key: your_generated_api_key
      description: "Development API key"
      created_at: "2024-03-21"
      expires_at: "2024-06-21"  # Optional
```

### Security Best Practices
1. Never commit API keys to version control
2. Rotate API keys regularly (recommended every 90 days)
3. Use different API keys for different environments (development, staging, production)
4. Implement API key expiration
5. Monitor API key usage for suspicious activity
6. Store API key hashes instead of plain text keys
7. Use environment-specific API keys
8. Implement rate limiting per API key

### API Key Validation
```python
import hashlib
from datetime import datetime, timedelta

def validate_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Validate an API key against its stored hash
    """
    return hashlib.sha256(api_key.encode()).hexdigest() == stored_hash

def is_api_key_expired(created_at: datetime, expires_in_days: int = 90) -> bool:
    """
    Check if an API key has expired
    """
    expiration_date = created_at + timedelta(days=expires_in_days)
    return datetime.now() > expiration_date
```

### Example API Key Management System
```python
from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import hashlib

class APIKeyManager:
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
    
    def generate_key(self, description: str, expires_in_days: int = 90) -> str:
        """
        Generate a new API key
        """
        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store key information
        self.api_keys[token_hash] = {
            'description': description,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=expires_in_days),
            'last_used': None,
            'usage_count': 0
        }
        
        return token
    
    def validate_key(self, api_key: str) -> bool:
        """
        Validate an API key
        """
        token_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if token_hash not in self.api_keys:
            return False
            
        key_info = self.api_keys[token_hash]
        
        # Check if key has expired
        if datetime.now() > key_info['expires_at']:
            return False
            
        # Update usage information
        key_info['last_used'] = datetime.now()
        key_info['usage_count'] += 1
        
        return True
    
    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key
        """
        token_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if token_hash in self.api_keys:
            del self.api_keys[token_hash]
            return True
        return False

# Example usage
api_manager = APIKeyManager()

# Generate a new API key
api_key = api_manager.generate_key("Development API Key")
print(f"Generated API Key: {api_key}")

# Validate the API key
is_valid = api_manager.validate_key(api_key)
print(f"API Key is valid: {is_valid}")

# Revoke the API key
api_manager.revoke_key(api_key)
```

## Endpoints

### 1. Configuration Management

#### Update Configuration
```http
POST /api/config
```

Request:
```json
{
  "project_path": "/path/to/project",
  "platform": "cursor|windsurf",
  "debug": true|false,
  "inactivity_delay": 300,
  "send_message": "your message here",
  "keystrokes": {
    "cursor": ["keystroke1", "keystroke2"],
    "windsurf": ["keystroke1", "keystroke2"]
  }
}
```

Success Response:
```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "config": {
    "project_path": "/path/to/project",
    "platform": "cursor",
    "debug": false,
    "inactivity_delay": 300,
    "send_message": "your message here",
    "keystrokes": {
      "cursor": ["keystroke1", "keystroke2"],
      "windsurf": ["keystroke1", "keystroke2"]
    }
  }
}
```

Error Response:
```json
{
  "status": "error",
  "message": "Invalid configuration",
  "errors": [
    "Invalid platform specified",
    "Project path does not exist"
  ]
}
```

#### Get Current Configuration
```http
GET /api/config
```

Success Response:
```json
{
  "status": "success",
  "config": {
    "project_path": "/path/to/project",
    "platform": "cursor",
    "debug": false,
    "inactivity_delay": 300,
    "send_message": "your message here",
    "keystrokes": {
      "cursor": ["keystroke1", "keystroke2"],
      "windsurf": ["keystroke1", "keystroke2"]
    }
  }
}
```

### 2. Screenshot Management

#### Get Screenshot
```http
GET /api/screenshot
```

Request:
```json
{
  "platform": "cursor|windsurf",
  "format": "png|jpeg",
  "quality": 85,  // Optional, for JPEG format
  "region": {     // Optional, for partial screenshots
    "x": 0,
    "y": 0,
    "width": 1920,
    "height": 1080
  }
}
```

Success Response:
```json
{
  "status": "success",
  "screenshot": {
    "url": "https://example.com/screenshots/123.png",
    "timestamp": "2024-03-21T12:00:00Z",
    "platform": "cursor",
    "dimensions": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

Error Response:
```json
{
  "status": "error",
  "message": "Failed to capture screenshot",
  "errors": [
    "Platform not found",
    "Invalid region specified"
  ]
}
```

## Usage Examples

### Python Examples

#### Basic Configuration Update
```python
import requests

def update_config(api_key, config_data):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'http://localhost:5000/api/config',
        headers=headers,
        json=config_data
    )
    
    return response.json()

# Example usage
config = {
    "project_path": "/path/to/project",
    "platform": "cursor",
    "debug": False,
    "inactivity_delay": 300,
    "send_message": "Hello, World!",
    "keystrokes": {
        "cursor": ["ctrl+s", "enter"],
        "windsurf": ["cmd+s", "enter"]
    }
}

result = update_config("your_api_key", config)
print(result)
```

#### Screenshot Capture and Download
```python
import requests
from datetime import datetime

def capture_screenshot(api_key, platform="cursor", format="png"):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    params = {
        "platform": platform,
        "format": format
    }
    
    response = requests.get(
        'http://localhost:5000/api/screenshot',
        headers=headers,
        json=params
    )
    
    data = response.json()
    
    if data['status'] == 'success':
        # Download the screenshot
        screenshot_url = data['screenshot']['url']
        image_response = requests.get(screenshot_url)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{platform}_{timestamp}.{format}"
        
        with open(filename, 'wb') as f:
            f.write(image_response.content)
        
        return filename
    
    return None

# Example usage
screenshot_file = capture_screenshot("your_api_key")
if screenshot_file:
    print(f"Screenshot saved as: {screenshot_file}")
```

### JavaScript Examples

#### Configuration Management
```javascript
async function updateConfig(apiKey, configData) {
    const response = await fetch('http://localhost:5000/api/config', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    });
    
    return await response.json();
}

// Example usage
const config = {
    project_path: "/path/to/project",
    platform: "cursor",
    debug: false,
    inactivity_delay: 300,
    send_message: "Hello, World!",
    keystrokes: {
        cursor: ["ctrl+s", "enter"],
        windsurf: ["cmd+s", "enter"]
    }
};

updateConfig("your_api_key", config)
    .then(result => console.log(result))
    .catch(error => console.error(error));
```

#### Screenshot Display
```javascript
async function displayScreenshot(apiKey, platform = "cursor") {
    const response = await fetch('http://localhost:5000/api/screenshot', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ platform, format: "png" })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
        const img = document.createElement('img');
        img.src = data.screenshot.url;
        img.alt = `${platform} Screenshot`;
        document.body.appendChild(img);
    }
}

// Example usage
displayScreenshot("your_api_key");
```

## Test Cases

### Configuration Tests

```python
import pytest
import requests

def test_update_config():
    # Test valid configuration
    valid_config = {
        "project_path": "/valid/path",
        "platform": "cursor",
        "debug": False,
        "inactivity_delay": 300
    }
    response = update_config("test_api_key", valid_config)
    assert response["status"] == "success"
    
    # Test invalid platform
    invalid_config = valid_config.copy()
    invalid_config["platform"] = "invalid_platform"
    response = update_config("test_api_key", invalid_config)
    assert response["status"] == "error"
    assert "Invalid platform specified" in response["errors"]
    
    # Test missing required field
    incomplete_config = valid_config.copy()
    del incomplete_config["project_path"]
    response = update_config("test_api_key", incomplete_config)
    assert response["status"] == "error"
    assert "Missing required field" in response["errors"]

def test_get_config():
    # Test successful retrieval
    response = get_config("test_api_key")
    assert response["status"] == "success"
    assert "config" in response
    
    # Test invalid API key
    response = get_config("invalid_key")
    assert response["status"] == "error"
    assert "Invalid API key" in response["errors"]
```

### Screenshot Tests

```python
def test_capture_screenshot():
    # Test successful capture
    response = capture_screenshot("test_api_key")
    assert response["status"] == "success"
    assert "screenshot" in response
    assert "url" in response["screenshot"]
    
    # Test invalid platform
    response = capture_screenshot("test_api_key", platform="invalid_platform")
    assert response["status"] == "error"
    assert "Platform not found" in response["errors"]
    
    # Test invalid region
    response = capture_screenshot(
        "test_api_key",
        region={"x": -1, "y": -1, "width": 0, "height": 0}
    )
    assert response["status"] == "error"
    assert "Invalid region specified" in response["errors"]
```

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Bad Request | Check request parameters and format |
| 401 | Unauthorized | Verify API key is valid and included |
| 403 | Forbidden | Check permissions and access rights |
| 404 | Not Found | Verify endpoint URL and resource existence |
| 500 | Internal Server Error | Contact system administrator |

## Rate Limiting
- Maximum 100 requests per minute per API key
- Maximum 10 screenshot requests per minute per API key
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time until limit resets

## Best Practices
1. Always include the API key in the Authorization header
2. Handle rate limiting by implementing exponential backoff
3. Validate configuration data before sending
4. Implement proper error handling for all API calls
5. Cache configuration when possible to reduce API calls
6. Use appropriate image formats based on use case
7. Implement retry logic for failed requests
8. Monitor API usage and adjust rate limits as needed 