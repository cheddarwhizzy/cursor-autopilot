# OpenAI Vision Integration

## Overview

Cursor Autopilot integrates with OpenAI's Vision API to analyze screenshots of the IDE and make decisions based on visual content. This integration allows for intelligent automation based on what's visible in the IDE.

## Configuration

### Basic Setup

Add the following to your `config.yaml`:

```yaml
openai:
  api_key: "your-api-key"
  vision:
    enabled: true
    model: "gpt-4-vision-preview"
    max_tokens: 300
    conditions:
      - trigger: "file_type"
        value: "python"
        question: "Is there a function definition in this code?"
        actions:
          true: ["ctrl+enter", "enter"]
          false: ["tab", "enter"]
      - trigger: "user_action"
        value: "save"
        question: "Has the file been saved successfully?"
        actions:
          true: ["ctrl+enter"]
          false: ["ctrl+s", "enter"]
```

### Vision Conditions Syntax

Conditions are defined in the `conditions` array under `vision` in the config. Each condition has the following structure:

```yaml
- trigger: "condition_type"  # Type of condition to check
  value: "condition_value"   # Value to match against
  question: "prompt"         # Question to ask about the screenshot
  actions:                   # Actions to take based on the answer
    true: ["keystroke1", "keystroke2"]
    false: ["keystroke3", "keystroke4"]
```

#### Supported Triggers

1. **File Type**
   - Triggers when a file of a specific type is opened/edited
   - Example: `trigger: "file_type", value: "python"`

2. **User Action**
   - Triggers on specific user actions
   - Example: `trigger: "user_action", value: "save"`

3. **Time Based**
   - Triggers after a specific duration of inactivity
   - Example: `trigger: "time", value: "300"` (seconds)

4. **Content Based**
   - Triggers when specific content is detected
   - Example: `trigger: "content", value: "error"`

### Question Formatting

The `question` field should be clear and specific to get accurate responses:

```yaml
question: |
  Is there a function definition in this code?
  If yes, what is the function name?
  If no, is there any code at all?
```

### Action Sequences

Actions are defined as arrays of keystrokes:

```yaml
actions:
  true:  # Actions when condition is met
    - "ctrl+enter"  # Send current line
    - "enter"       # New line
  false: # Actions when condition is not met
    - "tab"         # Indent
    - "enter"       # New line
```

## Examples

### 1. Function Detection

```yaml
- trigger: "file_type"
  value: "python"
  question: |
    Is there a function definition in this code?
    Look for 'def' keyword followed by a function name.
  actions:
    true:
      - "ctrl+enter"  # Run the function
      - "enter"       # New line
    false:
      - "tab"         # Indent
      - "enter"       # New line
```

### 2. Error Detection

```yaml
- trigger: "content"
  value: "error"
  question: |
    Is there a Python error message visible?
    Look for 'Error:', 'Exception:', or red text.
  actions:
    true:
      - "ctrl+enter"  # Try to fix
      - "enter"       # New line
    false:
      - "tab"         # Continue coding
      - "enter"       # New line
```

### 3. Save Confirmation

```yaml
- trigger: "user_action"
  value: "save"
  question: |
    Has the file been saved successfully?
    Look for a save indicator or confirmation message.
  actions:
    true:
      - "ctrl+enter"  # Run after save
    false:
      - "ctrl+s"      # Try saving again
      - "enter"       # Confirm
```

## API Key Setup

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add it to your `config.yaml`:
   ```yaml
   openai:
     api_key: "sk-..."
   ```
3. Set up environment variable (optional):
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify the key is correct
   - Check billing status
   - Ensure the key has vision access

2. **Vision Not Triggering**
   - Check condition syntax
   - Verify trigger values
   - Enable debug mode

3. **Incorrect Responses**
   - Refine question wording
   - Adjust max_tokens
   - Check screenshot quality

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
openai:
  vision:
    debug: true
```

This will log:
- Condition evaluations
- Screenshot captures
- API responses
- Action sequences

### Error Messages

1. **API Errors**
   ```
   Error: OpenAI API error - Invalid API key
   Solution: Check your API key in config.yaml
   ```

2. **Vision Errors**
   ```
   Error: Vision condition failed - Invalid trigger
   Solution: Check condition syntax in config.yaml
   ```

3. **Action Errors**
   ```
   Error: Action sequence failed - Invalid keystroke
   Solution: Verify keystroke format in actions
   ```

## Best Practices

1. **Question Design**
   - Be specific and clear
   - Include context
   - Ask for binary responses when possible

2. **Condition Design**
   - Use appropriate triggers
   - Keep conditions simple
   - Test thoroughly

3. **Action Design**
   - Use minimal keystrokes
   - Include error handling
   - Test on all platforms

4. **Performance**
   - Limit vision calls
   - Cache responses
   - Use appropriate timeouts

## Security

1. **API Key Protection**
   - Use environment variables
   - Never commit keys
   - Rotate keys regularly

2. **Data Privacy**
   - Screenshots are temporary
   - No sensitive data in questions
   - Secure API communication

## Integration Examples

### Python

```python
from openai import OpenAI
import base64
from PIL import Image
import io

def analyze_screenshot(image_path, question):
    client = OpenAI(api_key=config["openai"]["api_key"])
    
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content
```

### JavaScript

```javascript
async function analyzeScreenshot(imagePath, question) {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${config.openai.api_key}`
        },
        body: JSON.stringify({
            model: 'gpt-4-vision-preview',
            messages: [
                {
                    role: 'user',
                    content: [
                        { type: 'text', text: question },
                        {
                            type: 'image_url',
                            image_url: {
                                url: `data:image/jpeg;base64,${base64Image}`
                            }
                        }
                    ]
                }
            ],
            max_tokens: 300
        })
    });
    
    return await response.json();
}
``` 