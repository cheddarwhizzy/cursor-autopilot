# Slack API Integration

## Overview

Cursor Autopilot provides a set of RESTful endpoints that can be integrated with Slack to enable remote control and monitoring of the automation process. These endpoints are designed to be compatible with Slack's Block Kit and follow Slack's best practices for error handling and response formatting.

## Setup Instructions

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter an app name and select your workspace
5. Under "Add features and functionality", enable:
   - Slash Commands
   - Incoming Webhooks
   - Event Subscriptions

### 2. Configure App Permissions

1. Go to "OAuth & Permissions"
2. Add the following scopes:
   - `chat:write` - Send messages
   - `files:write` - Upload files
   - `commands` - Handle slash commands

### 3. Install the App

1. Click "Install to Workspace"
2. Authorize the app
3. Save the Bot User OAuth Token

### 4. Configure Cursor Autopilot

Add the following to your `config.yaml`:

```yaml
slack:
  bot_token: "xoxb-your-bot-token"
  signing_secret: "your-signing-secret"
  webhook_url: "https://hooks.slack.com/services/your/webhook/url"
```

## API Endpoints

### 1. Enable/Disable Auto Mode

**Endpoint:** `POST /api/slack/auto`

Toggle automatic keystroke sending.

#### Request

```json
{
  "command": "/auto",
  "text": "on|off",
  "response_url": "https://hooks.slack.com/commands/your/response/url"
}
```

#### Response

Success:
```json
{
  "response_type": "in_channel",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Auto mode has been *enabled*"
      }
    }
  ]
}
```

Error:
```json
{
  "response_type": "ephemeral",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Error: Invalid command format. Use `/auto on` or `/auto off`"
      }
    }
  ]
}
```

### 2. Get Screenshot

**Endpoint:** `POST /api/slack/screenshot`

Capture and upload a screenshot of the IDE.

#### Request

```json
{
  "command": "/screenshot",
  "text": "cursor|windsurf",
  "response_url": "https://hooks.slack.com/commands/your/response/url"
}
```

#### Response

Success:
```json
{
  "response_type": "in_channel",
  "blocks": [
    {
      "type": "image",
      "title": {
        "type": "plain_text",
        "text": "IDE Screenshot"
      },
      "image_url": "https://example.com/screenshots/123.png",
      "alt_text": "IDE Screenshot"
    }
  ]
}
```

Error:
```json
{
  "response_type": "ephemeral",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Error: Failed to capture screenshot. Platform not found."
      }
    }
  ]
}
```

### 3. Set Timeout

**Endpoint:** `POST /api/slack/timeout`

Set the inactivity delay before sending continuation prompts.

#### Request

```json
{
  "command": "/timeout",
  "text": "300",
  "response_url": "https://hooks.slack.com/commands/your/response/url"
}
```

#### Response

Success:
```json
{
  "response_type": "in_channel",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Inactivity delay set to *300* seconds"
      }
    }
  ]
}
```

Error:
```json
{
  "response_type": "ephemeral",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Error: Invalid timeout value. Must be a positive number."
      }
    }
  ]
}
```

### 4. Set Prompt

**Endpoint:** `POST /api/slack/prompt`

Set the initial or continuation prompt.

#### Request

```json
{
  "command": "/prompt",
  "text": "initial|continue Your prompt text here",
  "response_url": "https://hooks.slack.com/commands/your/response/url"
}
```

#### Response

Success:
```json
{
  "response_type": "in_channel",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Prompt updated successfully"
      }
    }
  ]
}
```

Error:
```json
{
  "response_type": "ephemeral",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Error: Invalid prompt format. Use `/prompt initial|continue Your text`"
      }
    }
  ]
}
```

## Error Codes and Handling

The API uses standard HTTP status codes and provides detailed error messages:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Invalid or missing authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

All error responses include:
- Error message
- Error code
- Suggested action (if applicable)

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute per workspace
- 1000 requests per hour per workspace

Rate limit responses include:
- Current limit
- Remaining requests
- Reset time

## Security

### Authentication
- All requests must include a valid Slack signing secret
- Requests are verified using Slack's signature verification
- Bot tokens are required for certain operations

### Data Protection
- No sensitive data is stored
- Screenshots are temporary and deleted after sending
- All communication is encrypted (HTTPS)

## Troubleshooting

### Common Issues

1. **Command not working**
   - Verify the app is installed in your workspace
   - Check the bot token in config.yaml
   - Ensure the app has the required permissions

2. **Screenshot failures**
   - Verify the platform is running
   - Check file permissions
   - Ensure the webhook URL is correct

3. **Rate limiting**
   - Check your current rate limit status
   - Implement exponential backoff
   - Consider caching responses

### Debug Mode

Enable debug mode in `config.yaml` to get detailed logs:

```yaml
slack:
  debug: true
```

## Examples

### Python Integration

```python
import requests
import json

def send_slack_command(command, text, response_url):
    payload = {
        "command": command,
        "text": text,
        "response_url": response_url
    }
    
    response = requests.post(
        "http://localhost:5000/api/slack/command",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()
```

### JavaScript Integration

```javascript
async function sendSlackCommand(command, text, responseUrl) {
    const response = await fetch('http://localhost:5000/api/slack/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            command,
            text,
            response_url: responseUrl
        })
    });
    
    return await response.json();
}
```

### cURL Examples

```bash
# Enable auto mode
curl -X POST http://localhost:5000/api/slack/auto \
     -H "Content-Type: application/json" \
     -d '{"command": "/auto", "text": "on"}'

# Get screenshot
curl -X POST http://localhost:5000/api/slack/screenshot \
     -H "Content-Type: application/json" \
     -d '{"command": "/screenshot", "text": "cursor"}'
``` 