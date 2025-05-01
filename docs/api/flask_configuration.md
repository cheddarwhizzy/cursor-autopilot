# Flask API Configuration

## Error Responses

### Format
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

### Common Error Codes

| Status Code | Error Message | Description |
|------------|--------------|-------------|
| 400 | Invalid configuration | Request body is malformed or missing required fields |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Rate limit exceeded or insufficient permissions |
| 404 | Resource not found | Requested resource (e.g., platform) does not exist |
| 422 | Validation error | Configuration values are invalid |
| 429 | Too many requests | Rate limit exceeded |
| 500 | Internal server error | Server-side error occurred |

### Example Error Responses

1. **Invalid Platform**
```json
{
  "status": "error",
  "message": "Invalid platform specified",
  "errors": [
    "Platform 'invalid_platform' is not supported",
    "Supported platforms: cursor, windsurf"
  ]
}
```

2. **Missing Required Field**
```json
{
  "status": "error",
  "message": "Missing required field",
  "errors": [
    "Field 'project_path' is required",
    "Field 'platform' is required"
  ]
}
```

3. **Validation Error**
```json
{
  "status": "error",
  "message": "Validation error",
  "errors": [
    "inactivity_delay must be a positive integer",
    "project_path must be an existing directory"
  ]
}
```

## Authentication

### API Key Requirement

1. **Obtaining an API Key**
   - Generate a new API key in the admin panel
   - Store the key securely (e.g., environment variable)
   - Never commit the key to version control

2. **Using the API Key**
   ```bash
   # Set as environment variable
   export CURSOR_AUTOPILOT_API_KEY="your-api-key"
   
   # Use in requests
   curl -H "Authorization: Bearer $CURSOR_AUTOPILOT_API_KEY" \
        -H "Content-Type: application/json" \
        -X POST http://localhost:5000/api/config \
        -d '{"project_path": "/path/to/project", "platform": "cursor"}'
   ```

### Rate Limiting

1. **Default Limits**
   - 100 requests per minute per API key
   - 1000 requests per hour per API key
   - 10000 requests per day per API key

2. **Rate Limit Headers**
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 99
   X-RateLimit-Reset: 1625097600
   ```

3. **Exceeding Limits**
   ```json
   {
     "status": "error",
     "message": "Rate limit exceeded",
     "errors": [
       "Too many requests. Please try again in 60 seconds."
     ],
     "retry_after": 60
   }
   ```

### Request Validation

1. **Required Headers**
   ```
   Authorization: Bearer <api_key>
   Content-Type: application/json
   ```

2. **Request Body Validation**
   - All fields must be of correct type
   - Required fields must be present
   - Values must be within allowed ranges
   - Platform-specific requirements must be met

## Common Configuration Scenarios

### 1. Setting Up a New Project

```bash
# 1. Create project directory
mkdir my_project
cd my_project

# 2. Initialize configuration
curl -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5000/api/config \
     -d '{
       "project_path": "/path/to/my_project",
       "platform": "cursor",
       "inactivity_delay": 300,
       "send_message": true,
       "keystrokes": {
         "cursor": ["command+p", "enter"]
       }
     }'
```

### 2. Updating Keystrokes

```bash
# Update keystrokes for Cursor
curl -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5000/api/config \
     -d '{
       "keystrokes": {
         "cursor": [
           {"keys": "command+p", "delay_ms": 100},
           {"keys": "enter", "delay_ms": 50}
         ]
       }
     }'
```

### 3. Modifying Platform Settings

```bash
# Enable both platforms
curl -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5000/api/config \
     -d '{
       "platform": "cursor,windsurf",
       "inactivity_delay": 300,
       "send_message": true
     }'
```

## Configuration Validation Rules

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| project_path | string | Path to project directory |
| platform | string | Comma-separated list of platforms |
| inactivity_delay | integer | Delay in seconds before timeout |

### Field Types and Formats

1. **project_path**
   - Type: string
   - Must be absolute path
   - Must exist and be a directory
   - Must be readable and writable

2. **platform**
   - Type: string
   - Comma-separated list
   - Valid values: "cursor", "windsurf"
   - At least one platform required

3. **inactivity_delay**
   - Type: integer
   - Must be positive
   - Minimum: 60 seconds
   - Maximum: 3600 seconds

4. **keystrokes**
   - Type: object
   - Keys: platform names
   - Values: arrays of keystroke objects
   - Each keystroke object must have:
     - keys: string
     - delay_ms: integer

### Platform-Specific Requirements

1. **Cursor**
   - Requires macOS, Windows, or Linux
   - Must have Cursor IDE installed
   - Must have appropriate permissions

2. **Windsurf**
   - Requires macOS or Windows
   - Must have Windsurf IDE installed
   - Must have appropriate permissions

## Troubleshooting Guide

### Common Error Messages

1. **"Project path does not exist"**
   - Verify the path is correct
   - Check permissions
   - Ensure directory exists

2. **"Invalid platform specified"**
   - Check platform spelling
   - Verify platform is installed
   - Check platform compatibility

3. **"Rate limit exceeded"**
   - Check rate limit headers
   - Implement exponential backoff
   - Consider increasing rate limits

### Configuration Conflicts

1. **Platform Conflicts**
   - Only one platform can be active at a time
   - Use platform-specific settings
   - Check platform compatibility

2. **Keystroke Conflicts**
   - Avoid duplicate keystrokes
   - Use platform-specific mappings
   - Test keystrokes manually

### Platform-Specific Issues

1. **macOS**
   - Check accessibility permissions
   - Verify AppleScript permissions
   - Test window activation

2. **Windows**
   - Check UAC settings
   - Verify window focus
   - Test keystroke sending

3. **Linux**
   - Check X11 permissions
   - Verify wmctrl installation
   - Test window management

### Debug Mode

Enable debug logging in requests:
```bash
curl -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:5000/api/config \
     -d '{"debug": true}'
```

Check server logs for detailed error information. 