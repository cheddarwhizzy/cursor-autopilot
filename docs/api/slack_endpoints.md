# Slack API Endpoints

## Overview

The Cursor Autopilot system provides a set of Slack API endpoints for integration with Slack workspaces. These endpoints handle various automation commands, status updates, and notifications between the IDE and Slack.

## Authentication

All endpoints require authentication using the Slack bot token and app token configured in the `config.yaml` file. These tokens must have the appropriate OAuth scopes for the required functionality.

### Required Scopes

- `chat:write` - Send messages to channels
- `commands` - Create and respond to slash commands
- `files:write` - Upload files (for screenshots)
- `channels:history` - Read channel messages
- `channels:read` - View basic channel information

## Endpoints

### Command Handling

#### POST `/api/slack/commands`

Handles incoming Slack slash commands.

**Request Body:**
```json
{
  "command": "/cursor",
  "text": "command_name [arguments]",
  "user_id": "U0123456789",
  "channel_id": "C0123456789",
  "team_id": "T0123456789"
}
```

**Response:**
```json
{
  "response_type": "in_channel",
  "text": "Command processed successfully"
}
```

**Supported Commands:**
- `/cursor enable_auto` - Enable automatic mode
- `/cursor disable_auto` - Disable automatic mode
- `/cursor screenshot` - Take a screenshot of the IDE
- `/cursor set_timeout <seconds>` - Set continuation prompt timeout
- `/cursor set_prompt <prompt_text>` - Set continuation or initial prompt

### Event Subscriptions

#### POST `/api/slack/events`

Handles Slack events using the Events API.

**Request Body:**
```json
{
  "type": "event_callback",
  "event": {
    "type": "message",
    "channel": "C0123456789",
    "user": "U0123456789",
    "text": "message content",
    "ts": "1234567890.123456"
  }
}
```

**Response:**
```json
{
  "ok": true
}
```

**Supported Events:**
- `message` - Process channel messages
- `app_mention` - Handle bot mentions
- `reaction_added` - Process emoji reactions

### Interactive Components

#### POST `/api/slack/interactivity`

Handles interactive message components like buttons and modals.

**Request Body:**
```json
{
  "type": "block_actions",
  "user": {
    "id": "U0123456789"
  },
  "actions": [{
    "action_id": "action_identifier",
    "value": "selected_value"
  }]
}
```

**Response:**
```json
{
  "response_type": "in_channel",
  "replace_original": true,
  "text": "Action processed successfully"
}
```

### File Upload

#### POST `/api/slack/files/upload`

Uploads files (such as screenshots) to Slack channels.

**Request Body (multipart/form-data):**
```
file: [binary file data]
channels: C0123456789
title: Screenshot 2024-03-21
```

**Response:**
```json
{
  "ok": true,
  "file": {
    "id": "F0123456789",
    "url_private": "https://files.slack.com/..."
  }
}
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "ok": false,
  "error": "error_code",
  "error_message": "Human-readable error description"
}
```

Common error codes:
- `invalid_auth` - Invalid or expired tokens
- `missing_scope` - Missing required OAuth scopes
- `channel_not_found` - Invalid channel ID
- `rate_limited` - Too many requests
- `invalid_arguments` - Invalid command arguments

## Rate Limiting

- Default rate limit: 50 requests per minute per workspace
- File upload rate limit: 20 uploads per minute
- Endpoints use standard Slack API rate limiting headers:
  - `Retry-After`: Seconds to wait before retrying
  - `X-Rate-Limit-Limit`: Total allowed requests
  - `X-Rate-Limit-Remaining`: Remaining requests
  - `X-Rate-Limit-Reset`: Timestamp when limit resets

## Best Practices

1. **Error Handling**
   - Always check response status codes
   - Implement exponential backoff for rate limits
   - Log detailed error information

2. **Performance**
   - Cache channel and user information
   - Batch updates when possible
   - Use RTM API for real-time requirements

3. **Security**
   - Validate all incoming requests
   - Use environment variables for tokens
   - Implement request signing verification

4. **Maintenance**
   - Monitor API usage and rate limits
   - Keep tokens and scopes up to date
   - Regular testing of all endpoints

## Example Usage

### Command Processing

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=BOT_TOKEN)

try:
    # Handle enable_auto command
    response = client.chat_postMessage(
        channel=channel_id,
        text="Automatic mode enabled",
        thread_ts=thread_ts
    )
except SlackApiError as e:
    print(f"Error: {e.response['error']}")
```

### Event Handling

```python
@app.event("app_mention")
def handle_mention(event, say):
    try:
        say(
            text="I received your mention!",
            thread_ts=event.get("thread_ts", event["ts"])
        )
    except Exception as e:
        print(f"Error handling mention: {str(e)}")
```

## Testing

The API includes a set of test endpoints for verifying integration:

### GET `/api/slack/test`

Tests basic connectivity and authentication.

**Response:**
```json
{
  "ok": true,
  "authenticated": true,
  "bot_user_id": "U0123456789"
}
```

### POST `/api/slack/test/command`

Tests command processing without affecting production channels.

**Request Body:**
```json
{
  "command": "/cursor",
  "text": "test_command",
  "channel_id": "C0123456789"
}
```

**Response:**
```json
{
  "ok": true,
  "command_received": true
}
``` 