# Project Tasks

## New Feature Requirements: Configurable Automation & API Integration

### 1. YAML-Based Configuration
- [x] Migrate all configuration to a single YAML file (replacing/merging any existing config.json)
- [x] Support configuration of keystrokes, delays, and automation options via YAML
- [x] Allow separate, customizable keystroke sets for Cursor and Windsurf platforms
- [x] Add support for Windows and Ubuntu Desktop platforms (if programmatic keystroke sending is possible)
- [x] Implement platform-specific initialization keystrokes in YAML config
- [x] Add tests for YAML configuration loading and validation
- [x] Add documentation for YAML configuration options
  - [x] Create configuration schema documentation
  - [x] Add examples for different platforms
  - [x] Document validation rules
  - [x] Add troubleshooting guide
  - [x] Document Windows, OSX, and Linux setup in great detail
- [x] Implement cross-platform keystroke support
  - [x] Integrate `pyautogui` for sending keystrokes
  - [x] Implement logic to map generic keys (e.g., 'command') to platform-specific keys based on `os_type` (e.g., 'ctrl' for Windows/Linux)
  - [x] Test keystroke sending on macOS, Windows, and Linux
  - [x] Update `actions/send_to_cursor.py` (or relevant module) to use `pyautogui`

### 2. API Endpoints (for Slack Integration)
- [x] Implement POST endpoints to:
  - Enable/disable auto mode (toggle automatic keystroke sending)
  - Grab a screenshot of the IDE platform
  - Set the timeout for sending the continuation prompt
  - Set the continuation or initial prompt
- [x] Endpoints should be Slack-app compatible (JSON responses, Slack-friendly error handling)
- [x] Add tests for Slack integration
- [x] Add documentation for Slack API endpoints
  - [x] Document endpoint specifications
  - [x] Add request/response examples
  - [x] Document error codes and handling
  - [x] Add setup instructions for Slack app

### 2.1 Flask API Configuration Endpoints
- [x] Add documentation for Flask API configuration endpoints
  - [x] Document configuration endpoints
    ```json
    POST /api/config
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
  - [x] Document screenshot endpoints
    ```json
    GET /api/screenshot
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
    Response:
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
    Usage Examples:
    ```python
    # Python example using requests
    import requests
    
    # Get screenshot
    response = requests.get('http://localhost:5000/api/screenshot', 
                          json={'platform': 'cursor', 'format': 'png'})
    data = response.json()
    
    if data['status'] == 'success':
        # Download the screenshot
        screenshot_url = data['screenshot']['url']
        image_response = requests.get(screenshot_url)
        with open('screenshot.png', 'wb') as f:
            f.write(image_response.content)
    ```
    ```javascript
    // JavaScript example using fetch
    async function getScreenshot() {
      const response = await fetch('http://localhost:5000/api/screenshot', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          platform: 'cursor',
          format: 'png'
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Display the screenshot in an img element
        const img = document.createElement('img');
        img.src = data.screenshot.url;
        document.body.appendChild(img);
      }
    }
    ```
    ```bash
    # cURL example
    curl -X GET http://localhost:5000/api/screenshot \
         -H "Content-Type: application/json" \
         -d '{"platform": "cursor", "format": "png"}' \
         -o screenshot.png
    ```
    ```python
    # Python example for Slack integration
    def post_screenshot_to_slack(slack_webhook_url):
        # Get screenshot
        response = requests.get('http://localhost:5000/api/screenshot', 
                              json={'platform': 'cursor', 'format': 'png'})
        data = response.json()
        
        if data['status'] == 'success':
            # Post to Slack
            slack_payload = {
                "blocks": [
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": "IDE Screenshot"
                        },
                        "image_url": data['screenshot']['url'],
                        "alt_text": "IDE Screenshot"
                    }
                ]
            }
            requests.post(slack_webhook_url, json=slack_payload)
    ```
  - [x] Document response format
    ```json
    {
      "status": "success|error",
      "message": "Configuration updated successfully",
      "config": {
        // Updated configuration
      }
    }
    ```
  - [x] Document error responses
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
  - [x] Add authentication requirements
    - [x] Document API key requirement
    - [x] Document rate limiting
    - [x] Document request validation
  - [x] Add examples for common configuration scenarios
    - [x] Setting up new project
    - [x] Updating keystrokes
    - [x] Modifying platform settings
  - [x] Document configuration validation rules
    - [x] Required fields
    - [x] Field types and formats
    - [x] Platform-specific requirements
  - [x] Add troubleshooting guide
    - [x] Common error messages
    - [x] Configuration conflicts
    - [x] Platform-specific issues

### 3. OpenAI Vision Integration
- [x] From YAML config, define conditions to trigger OpenAI Vision (e.g., file type, user action)
- [x] If condition is true, take a screenshot and ask a question; then run a set of keystrokes based on the result
- [x] If condition is false, run an alternate set of keystrokes
- [x] Ensure this workflow is compatible with Slack commands and API triggers
- [x] Add tests for OpenAI Vision integration
- [x] Add documentation for OpenAI Vision configuration
  - [x] Document vision conditions syntax
  - [x] Add examples for different file types
  - [x] Document API key setup
  - [x] Add troubleshooting guide

### 4. Migration
- [x] Remove and merge all config.json settings into the new YAML config
- [x] Document all YAML options and provide migration instructions
- [x] Add migration tests
- [x] Add validation for migrated configurations

### 5. Update run.sh for Config Flags
- [x] Add support to run.sh for accepting command-line flags to override config parameters, including:
  - `--project_path`
  - `--platform`
  - `--debug`
  - `--inactivity_delay`
  - `--send_message`
  - (and any other relevant config options)
- [x] Ensure CLI flags take precedence over YAML config values
- [x] Document usage examples in the README
- [x] Add tests for CLI flag parsing
- [x] Add validation for CLI flag values
- [x] Refactor CLI argument handling to Python using `argparse`
  - [x] Create a Python script (e.g., `cli.py` or integrate into main script) to handle argument parsing
  - [x] Define arguments using `argparse` corresponding to `config.yaml` settings
    - [x] `--project-path`: Override project path (string)
    - [x] `--platform`: Specify active platform(s) (string, comma-separated, e.g., "cursor,windsurf")
    - [x] `--inactivity-delay`: Override inactivity delay in seconds (integer)
    - [x] `--send-message`: Override send message flag (boolean flag, e.g., `--send-message` or `--no-send-message`)
    - [x] Add other relevant arguments as needed (e.g., `--debug`)
  - [x] Load `config.yaml` first, then override with CLI arguments
  - [x] Update `run.sh` to execute the Python script with arguments
  - [x] Ensure `--help` provides useful information

### 6. Simultaneous Automation
- [x] Support running Cursor and Windsurf at the same time
    - [x] Activate each app and send keystrokes to each in a staggered manner
    - [x] Ensure at least 90 seconds between sending inactivity/timeout continuation commands to Cursor and Windsurf if both are running
    - [x] Add detailed logging to track which app is being activated, when keystrokes are sent, and timing of inactivity triggers
    - [x] Prevent foreground conflicts by always ensuring one app's automation completes before switching
- [x] Add tests for simultaneous automation
- [x] Document simultaneous automation configuration
  - [x] Platform activation sequence
  - [x] Timing diagrams
  - [x] Conflict prevention
  - [x] Troubleshooting

### 7. Test Suite Documentation
- [x] Create comprehensive test suite documentation
  - [x] Document test categories and organization
  - [x] Add instructions for running tests
  - [x] Document test coverage requirements
  - [x] Add troubleshooting guide
  - [x] Document best practices
  - [x] Add CI/CD integration details

### 8. CI/CD Setup
- [x] Set up GitHub Actions workflow
  - [x] Configure test matrix for multiple platforms
  - [x] Add linting and formatting checks
  - [x] Add security scanning
  - [x] Add performance testing
  - [x] Configure coverage reporting
- [x] Create CI/CD documentation
  - [x] Document pipeline configuration
  - [x] Add local development setup
  - [x] Document best practices
  - [x] Add troubleshooting guide

## Test Coverage Improvements
- [x] Add comprehensive API endpoint tests
  - [x] Rate limiting implementation
  - [x] Authentication flow
  - [x] Request validation
  - [x] Response formatting
  - [x] Error handling
- [x] Add vision integration tests
  - [x] Vision condition evaluation
  - [x] Screenshot capture and processing
  - [x] Response handling
  - [x] Error cases
- [x] Add performance tests
  - [x] Concurrent operations
  - [x] Resource usage
  - [x] Response times
  - [x] Scalability
  - [x] Stress testing
- [x] Add edge case tests
  - [x] Invalid input handling
  - [x] Network failures
  - [x] Timeout scenarios
  - [x] Resource exhaustion

## Acceptance Criteria
- [x] All features must be fully tested
  - [x] Unit tests for core functionality
  - [x] Integration tests for complete workflow
  - [x] Performance tests for simultaneous automation
  - [x] Security tests for API endpoints
  - [x] Error handling tests
  - [x] Resource cleanup tests
  - [x] Logging and monitoring tests
- [x] Code coverage must be above 80%
- [x] Application must be responsive on all devices
- [x] All API endpoints must be documented
- [x] Security best practices must be followed
- [x] Performance must be optimized
- [x] Error handling must be comprehensive


## Blockers/Questions
- [x] Need to decide on specific UI component library
  - Recommendation: Use Material-UI (MUI) for React components
  - Justification: 
    - Follows Material Design principles
    - Extensive component library
    - Good TypeScript support
    - Active community and maintenance
    - Consistent with project's React guidelines

- [x] Need to determine database backup strategy
  - Recommendation: Implement automated daily backups with retention policy
  - Strategy:
    - Daily full backups
    - Weekly incremental backups
    - 30-day retention period
    - Encrypted backups stored in cloud storage
    - Automated backup verification
    - Point-in-time recovery capability

- [x] Need to finalize authentication requirements
  - Recommendation: Implement JWT-based authentication with refresh tokens
  - Requirements:
    - JWT for short-lived access tokens
    - Refresh token rotation
    - Secure password hashing (bcrypt)
    - Rate limiting
    - Session management
    - CORS configuration
    - API key management

- [x] Need to decide on monitoring solution
  - Recommendation: Use Prometheus + Grafana for monitoring
  - Components:
    - Prometheus for metrics collection
    - Grafana for visualization
    - Alertmanager for notifications
    - Structured logging with ELK stack
    - Application health checks
    - Performance monitoring
    - Error tracking

- [x] Need to add comprehensive test coverage for new features
  - Strategy:
    - Unit tests for all components (minimum 80% coverage)
    - Integration tests for API endpoints
    - E2E tests for critical paths
    - Mock external services
    - Automated test runs in CI/CD pipeline
    - Performance testing
    - Security testing

- [x] Need to add detailed documentation for new features
  - Documentation types:
    - JSDoc comments for code
    - API documentation (Swagger/OpenAPI)
    - Architecture diagrams
    - Development workflow guides
    - Deployment procedures
    - Troubleshooting guides
    - Security protocols
    - Backup procedures

## Documentation
- [x] Add easy-to-follow documentation to `README.md`
  - [x] Provide the simplest command to run the application at the top
  - [x] Briefly explain core concepts (config, tasks)
  - [x] Link to detailed documentation in the `docs/` folder for advanced users
- [x] Create quick start guide for new users
  - [x] Installation instructions
  - [x] Basic setup steps
  - [x] Configuration examples
  - [x] Common use cases
  - [x] Troubleshooting tips