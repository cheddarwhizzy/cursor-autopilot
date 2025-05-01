# Simultaneous Automation

## Overview

Cursor Autopilot supports running multiple IDE platforms (Cursor and Windsurf) simultaneously, with intelligent scheduling and conflict prevention to ensure smooth operation.

## Configuration

### Basic Setup

Add the following to your `config.yaml`:

```yaml
platforms:
  cursor:
    enabled: true
    activation_sequence: ["cmd+space", "cursor", "enter"]
    inactivity_delay: 300
    priority: 1
  windsurf:
    enabled: true
    activation_sequence: ["cmd+space", "windsurf", "enter"]
    inactivity_delay: 300
    priority: 2
```

### Platform Settings

Each platform can be configured with:

```yaml
platform_name:
  enabled: true|false          # Whether to run this platform
  activation_sequence: []      # Keystrokes to activate the platform
  inactivity_delay: 300        # Seconds before sending continuation prompt
  priority: 1                  # Order of activation (lower = higher priority)
  keystrokes:                  # Platform-specific keystrokes
    - "ctrl+enter"
    - "enter"
```

## Activation Sequence

### 1. Initial Activation

1. Start with highest priority platform (lowest number)
2. Wait for activation sequence to complete
3. Send initial keystrokes
4. Move to next platform
5. Repeat until all platforms are active

### 2. Inactivity Handling

1. Monitor all active platforms
2. When inactivity detected:
   - Wait for current platform to complete
   - Switch to inactive platform
   - Send continuation prompt
   - Return to previous platform

### 3. Conflict Prevention

1. **Foreground Locking**
   - Only one platform active at a time
   - Complete current action before switching
   - Maintain action queue per platform

2. **Timing Control**
   - Minimum 90s between platform switches
   - Staggered activation sequences
   - Priority-based scheduling

## Timing Diagrams

### 1. Initial Activation

```
Platform 1 (Priority 1)
|--Activate--|--Keystrokes--|--Complete--|
                    |
                    v
Platform 2 (Priority 2)
                    |--Activate--|--Keystrokes--|--Complete--|
```

### 2. Inactivity Handling

```
Platform 1
|--Active--|--Inactive--|--Switch--|--Active--|
                    |
                    v
Platform 2
                    |--Active--|--Prompt--|--Complete--|
```

### 3. Conflict Prevention

```
Platform 1
|--Action 1--|--Complete--|--Action 2--|--Complete--|
                    |
                    v
Platform 2
                    |--Wait--|--Action 1--|--Complete--|
```

## Best Practices

### 1. Platform Configuration

- Set appropriate priorities
- Configure unique activation sequences
- Adjust inactivity delays per platform

### 2. Timing Optimization

- Stagger activation sequences
- Set appropriate delays
- Monitor performance

### 3. Error Handling

- Implement retry logic
- Log all actions
- Handle timeouts

## Troubleshooting

### Common Issues

1. **Platform Not Activating**
   - Check activation sequence
   - Verify platform is installed
   - Check permissions

2. **Keystrokes Not Working**
   - Verify keystroke format
   - Check platform focus
   - Test manually

3. **Timing Issues**
   - Adjust delays
   - Check system load
   - Monitor logs

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
debug: true
```

This will log:
- Platform activation attempts
- Keystroke sequences
- Timing information
- Error details

### Error Messages

1. **Activation Errors**
   ```
   Error: Failed to activate platform - Timeout
   Solution: Check activation sequence and delays
   ```

2. **Keystroke Errors**
   ```
   Error: Keystroke failed - Platform not focused
   Solution: Verify platform activation
   ```

3. **Timing Errors**
   ```
   Error: Minimum delay not met - 90s required
   Solution: Adjust scheduling or delays
   ```

## Performance Optimization

### 1. System Resources

- Monitor CPU usage
- Check memory consumption
- Optimize timing

### 2. Platform Management

- Efficient switching
- Resource cleanup
- Error recovery

### 3. Logging

- Detailed logs
- Performance metrics
- Error tracking

## Security Considerations

### 1. Platform Access

- Secure activation
- Permission checks
- Access control

### 2. Data Protection

- Secure logging
- Error handling
- Resource cleanup

## Integration Examples

### Python

```python
class PlatformManager:
    def __init__(self, config):
        self.platforms = config["platforms"]
        self.active_platform = None
        self.last_switch = time.time()
    
    def activate_platform(self, platform_name):
        if time.time() - self.last_switch < 90:
            raise Exception("Minimum delay not met")
        
        platform = self.platforms[platform_name]
        for keystroke in platform["activation_sequence"]:
            send_keystroke(keystroke)
            time.sleep(0.5)
        
        self.active_platform = platform_name
        self.last_switch = time.time()
    
    def send_keystrokes(self, platform_name, keystrokes):
        if self.active_platform != platform_name:
            self.activate_platform(platform_name)
        
        for keystroke in keystrokes:
            send_keystroke(keystroke)
            time.sleep(0.1)
```

### JavaScript

```javascript
class PlatformManager {
    constructor(config) {
        this.platforms = config.platforms;
        this.activePlatform = null;
        this.lastSwitch = Date.now();
    }
    
    async activatePlatform(platformName) {
        if (Date.now() - this.lastSwitch < 90000) {
            throw new Error("Minimum delay not met");
        }
        
        const platform = this.platforms[platformName];
        for (const keystroke of platform.activation_sequence) {
            await sendKeystroke(keystroke);
            await sleep(500);
        }
        
        this.activePlatform = platformName;
        this.lastSwitch = Date.now();
    }
    
    async sendKeystrokes(platformName, keystrokes) {
        if (this.activePlatform !== platformName) {
            await this.activatePlatform(platformName);
        }
        
        for (const keystroke of keystrokes) {
            await sendKeystroke(keystroke);
            await sleep(100);
        }
    }
}
``` 