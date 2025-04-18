# Slack Bot Usage

The Slack bot listens for commands and enables remote control of Cursor Autopilot via your Slack workspace.

## Supported Commands

- `code` — Switch to code mode (manual control)
- `auto` — Switch to auto mode (autonomous operation)
- `send <your prompt>` — Send a prompt to Cursor
- `screenshot` — Capture a chat screenshot
- `status` — Get current mode

## Testing Locally

You can test the Slack bot's endpoints directly by sending POST requests to the running Flask server. Use the following `curl` commands to simulate Slack commands:

Replace `USER_NAME` with your desired username (optional).

### Enter Manual Mode (code)
```bash
curl -X POST http://localhost:5005/cursor -d 'text=code&user_name=USER_NAME'
```

### Enable Autonomous Coding (auto)
```bash
curl -X POST http://localhost:5005/cursor -d 'text=auto&user_name=USER_NAME'
```

### Send a Message to Cursor
```bash
curl -X POST http://localhost:5005/cursor -d 'text=send <your message here>&user_name=USER_NAME'
```

### Capture Chat Window Screenshot
```bash
curl -X POST http://localhost:5005/cursor -d 'text=screenshot&user_name=USER_NAME'
```

### Show Current Mode
```bash
curl -X POST http://localhost:5005/cursor -d 'text=status&user_name=USER_NAME'
```

These commands simulate the Slack slash commands as if used in Slack.
