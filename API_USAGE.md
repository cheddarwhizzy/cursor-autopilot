# Configuration API Usage Guide

## Overview

The Cursor Autopilot now includes a REST API for managing configuration settings programmatically. This allows you to update settings like `inactivity_delay`, platform configurations, and other settings through HTTP requests instead of manually editing the `config.yaml` file.

## Quick Start

### 1. Generate an API Key

```bash
python scripts/generate_api_key.py --description "My API Key" --days 30
```

This will output:
```
Generated API Key: abc123...
Description: My API Key
Expires: 30 days
Rate Limit: 100 requests/minute

Add this to your environment:
export CURSOR_AUTOPILOT_API_KEY='abc123...'
```

### 2. Set Environment Variable

```bash
export CURSOR_AUTOPILOT_API_KEY='your-generated-key'
```

### 3. Start the API Server

```bash
python src/api/app.py
```

The server will start on `http://localhost:5005` by default.

### 4. Test the API

```bash
python scripts/test_api.py
```

## API Endpoints

### Health Check
```bash
curl http://localhost:5005/health
```

### Get Current Configuration
```bash
curl -H "Authorization: Bearer $CURSOR_AUTOPILOT_API_KEY" \
     http://localhost:5005/api/config
```

### Update Inactivity Delay
```bash
curl -H "Authorization: Bearer $CURSOR_AUTOPILOT_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5005/api/config \
     -d '{
       "general": {
         "inactivity_delay": 300
       }
     }'
```

### Update Platform Settings
```bash
curl -H "Authorization: Bearer $CURSOR_AUTOPILOT_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5005/api/config \
     -d '{
       "platforms": {
         "cursor": {
           "initialization_delay_seconds": 8,
           "project_path": "/path/to/new/project"
         }
       }
     }'
```

### Update Multiple Settings at Once
```bash
curl -H "Authorization: Bearer $CURSOR_AUTOPILOT_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5005/api/config \
     -d '{
       "general": {
         "inactivity_delay": 180,
         "debug": true,
         "active_platforms": ["cursor", "windsurf_mushattention"]
       },
       "platforms": {
         "cursor": {
           "initialization_delay_seconds": 5
         }
       }
     }'
```

## Configuration Fields

### General Settings
- `inactivity_delay` (int): Seconds to wait before sending continuation prompt (60-3600)
- `debug` (bool): Enable debug logging
- `active_platforms` (array): List of platforms to activate
- `send_message` (bool): Whether to send messages automatically
- `use_vision_api` (bool): Enable OpenAI Vision API integration
- `use_gitignore` (bool): Use .gitignore patterns for file filtering
- `staggered` (bool): Enable staggered platform execution
- `stagger_delay` (int): Delay between staggered platform starts (1-300)
- `initial_delay` (int): Initial delay before starting automation (1-300)

### Platform Settings
Each platform can have these settings:
- `type` (string): Platform type ("cursor" or "windsurf")
- `window_title` (string): Window title to identify the application
- `project_path` (string): Path to the project directory
- `task_file_path` (string): Path to the task file relative to project_path
- `additional_context_path` (string): Path to additional context file
- `initialization_delay_seconds` (int): Seconds to wait for IDE initialization (1-30)

## Error Handling

The API returns standardized error responses:

```json
{
  "status": "error",
  "message": "Configuration validation failed",
  "errors": [
    "inactivity_delay must be at least 60",
    "project_path does not exist: /invalid/path"
  ]
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (malformed JSON)
- `401`: Unauthorized (missing/invalid API key)
- `422`: Validation error (invalid configuration values)
- `429`: Rate limit exceeded
- `500`: Internal server error

## Python Integration Example

```python
import requests
import os

# Setup
api_key = os.getenv('CURSOR_AUTOPILOT_API_KEY')
base_url = 'http://localhost:5005'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Get current configuration
response = requests.get(f'{base_url}/api/config', headers=headers)
config = response.json()['config']

# Update inactivity delay
update_data = {
    'general': {
        'inactivity_delay': 240
    }
}
response = requests.post(f'{base_url}/api/config', headers=headers, json=update_data)
result = response.json()

print(f"Updated: {result['updated_fields']}")
```

## Security Notes

1. **API Key Protection**: Never commit API keys to version control
2. **Environment Variables**: Store keys in environment variables or secure configuration
3. **Rate Limiting**: Each API key has a rate limit (default: 100 requests/minute)
4. **Network Security**: Use HTTPS in production environments
5. **Key Rotation**: Rotate API keys regularly (recommended every 90 days)

## Troubleshooting

### Server Not Starting
- Check if port 5005 is available
- Verify Python dependencies are installed
- Check for import errors in the logs

### Authentication Errors
- Verify API key is set correctly: `echo $CURSOR_AUTOPILOT_API_KEY`
- Check Authorization header format: `Bearer <key>`
- Ensure API key hasn't expired

### Validation Errors
- Check that numeric values are within valid ranges
- Verify file paths exist and are accessible
- Ensure platform types are valid ("cursor" or "windsurf")

### Configuration Not Saving
- Check file permissions on config.yaml
- Verify the API process has write access to the config directory
- Look for backup files (.backup extension) if writes are failing

## Next Steps

For more advanced features and future enhancements, see the [CONFIG_API_IMPLEMENTATION_PLAN.md](CONFIG_API_IMPLEMENTATION_PLAN.md) file. 