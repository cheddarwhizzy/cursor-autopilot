# Project Tasks

## Project Overview
Building a modern web application with React, TypeScript, and Node.js backend. The application will be a task management system with user authentication, real-time updates, and a clean, responsive UI.

## Current Sprint

### 1. Project Setup and Configuration
- [ ] Initialize project structure
  - [ ] Create frontend directory with React + TypeScript
  - [ ] Create backend directory with Node.js + Express
  - [ ] Set up TypeScript configuration for both frontend and backend
  - [ ] Configure ESLint and Prettier
  - [ ] Set up Git repository with proper .gitignore

### 2. Backend Development
- [ ] Set up Express server
  - [ ] Configure basic Express app with TypeScript
  - [ ] Set up middleware (cors, body-parser, etc.)
  - [ ] Implement error handling middleware
  - [ ] Set up logging system

- [ ] Database Setup
  - [ ] Set up PostgreSQL database
  - [ ] Create database schema
  - [ ] Implement database migrations
  - [ ] Set up connection pooling

- [ ] Authentication System
  - [ ] Implement JWT authentication
  - [ ] Create user registration endpoint
  - [ ] Create login endpoint
  - [ ] Implement password hashing
  - [ ] Add refresh token mechanism

### 3. Frontend Development
- [ ] Set up React application
  - [ ] Configure Vite with TypeScript
  - [ ] Set up routing with React Router
  - [ ] Implement state management with Redux Toolkit
  - [ ] Set up API client with Axios

- [ ] UI Components
  - [ ] Create reusable UI components
  - [ ] Implement responsive layout
  - [ ] Add loading states and error boundaries
  - [ ] Set up theme system

### 4. Core Features
- [ ] Task Management
  - [ ] Create task model and API endpoints
  - [ ] Implement task CRUD operations
  - [ ] Add task filtering and sorting
  - [ ] Implement task status updates

- [ ] User Interface
  - [ ] Create dashboard layout
  - [ ] Implement task list view
  - [ ] Add task creation form
  - [ ] Create task detail view

### 5. Testing
- [ ] Backend Testing
  - [ ] Set up Jest for backend tests
  - [ ] Write API endpoint tests
  - [ ] Implement database tests
  - [ ] Add authentication tests

- [ ] Frontend Testing
  - [ ] Set up React Testing Library
  - [ ] Write component tests
  - [ ] Implement integration tests
  - [ ] Add end-to-end tests with Cypress

### 6. Deployment
- [ ] Set up CI/CD pipeline
  - [ ] Configure GitHub Actions
  - [ ] Set up automated testing
  - [ ] Configure deployment to staging
  - [ ] Set up production deployment

- [ ] Infrastructure
  - [ ] Set up Docker containers
  - [ ] Configure Nginx
  - [ ] Set up SSL certificates
  - [ ] Configure monitoring

## New Feature Requirements: Configurable Automation & API Integration

### 1. YAML-Based Configuration
- [x] Migrate all configuration to a single YAML file (replacing/merging any existing config.json)
- [x] Support configuration of keystrokes, delays, and automation options via YAML
- [x] Allow separate, customizable keystroke sets for Cursor and Windsurf platforms
- [x] Add support for Windows and Ubuntu Desktop platforms (if programmatic keystroke sending is possible)
- [x] Implement platform-specific initialization keystrokes in YAML config
- [x] Add tests for YAML configuration loading and validation
- [ ] Add documentation for YAML configuration options
  - [ ] Create configuration schema documentation
  - [ ] Add examples for different platforms
  - [ ] Document validation rules
  - [ ] Add troubleshooting guide
  - [ ] Document Windows, OSX, and Linux setup in great detail
- [ ] Implement cross-platform keystroke support
  - [ ] Integrate `pyautogui` for sending keystrokes
  - [ ] Implement logic to map generic keys (e.g., 'command') to platform-specific keys based on `os_type` (e.g., 'ctrl' for Windows/Linux)
  - [ ] Test keystroke sending on macOS, Windows, and Linux
  - [ ] Update `actions/send_to_cursor.py` (or relevant module) to use `pyautogui`

### 2. API Endpoints (for Slack Integration)
- [x] Implement POST endpoints to:
  - Enable/disable auto mode (toggle automatic keystroke sending)
  - Grab a screenshot of the IDE platform
  - Set the timeout for sending the continuation prompt
  - Set the continuation or initial prompt
- [x] Endpoints should be Slack-app compatible (JSON responses, Slack-friendly error handling)
- [x] Add tests for Slack integration
- [ ] Add documentation for Slack API endpoints
  - [ ] Document endpoint specifications
  - [ ] Add request/response examples
  - [ ] Document error codes and handling
  - [ ] Add setup instructions for Slack app

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
  - [ ] Document error responses
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
  - [ ] Add authentication requirements
    - [ ] Document API key requirement
    - [ ] Document rate limiting
    - [ ] Document request validation
  - [ ] Add examples for common configuration scenarios
    - [ ] Setting up new project
    - [ ] Updating keystrokes
    - [ ] Modifying platform settings
  - [ ] Document configuration validation rules
    - [ ] Required fields
    - [ ] Field types and formats
    - [ ] Platform-specific requirements
  - [ ] Add troubleshooting guide
    - [ ] Common error messages
    - [ ] Configuration conflicts
    - [ ] Platform-specific issues

### 3. OpenAI Vision Integration
- [x] From YAML config, define conditions to trigger OpenAI Vision (e.g., file type, user action)
- [x] If condition is true, take a screenshot and ask a question; then run a set of keystrokes based on the result
- [x] If condition is false, run an alternate set of keystrokes
- [x] Ensure this workflow is compatible with Slack commands and API triggers
- [x] Add tests for OpenAI Vision integration
- [ ] Add documentation for OpenAI Vision configuration
  - [ ] Document vision conditions syntax
  - [ ] Add examples for different file types
  - [ ] Document API key setup
  - [ ] Add troubleshooting guide

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
- [ ] Refactor CLI argument handling to Python using `argparse`
  - [ ] Create a Python script (e.g., `cli.py` or integrate into main script) to handle argument parsing
  - [ ] Define arguments using `argparse` corresponding to `config.yaml` settings
    - [ ] `--project-path`: Override project path (string)
    - [ ] `--platform`: Specify active platform(s) (string, comma-separated, e.g., "cursor,windsurf")
    - [ ] `--inactivity-delay`: Override inactivity delay in seconds (integer)
    - [ ] `--send-message`: Override send message flag (boolean flag, e.g., `--send-message` or `--no-send-message`)
    - [ ] Add other relevant arguments as needed (e.g., `--debug`)
  - [ ] Load `config.yaml` first, then override with CLI arguments
  - [ ] Update `run.sh` to execute the Python script with arguments
  - [ ] Ensure `--help` provides useful information

### 6. Simultaneous Automation
- [x] Support running Cursor and Windsurf at the same time
    - [x] Activate each app and send keystrokes to each in a staggered manner
    - [x] Ensure at least 90 seconds between sending inactivity/timeout continuation commands to Cursor and Windsurf if both are running
    - [x] Add detailed logging to track which app is being activated, when keystrokes are sent, and timing of inactivity triggers
    - [x] Prevent foreground conflicts by always ensuring one app's automation completes before switching
- [x] Add tests for simultaneous automation
- [ ] Add documentation for simultaneous automation configuration
  - [ ] Document platform activation sequence
  - [ ] Add timing diagrams
  - [ ] Document conflict prevention
  - [ ] Add troubleshooting guide

## Acceptance Criteria
- All features must be fully tested
- Code coverage must be above 80%
- Application must be responsive on all devices
- All API endpoints must be documented
- Security best practices must be followed
- Performance must be optimized
- Error handling must be comprehensive


## Blockers/Questions
- Need to decide on specific UI component library
- Need to determine database backup strategy
- Need to finalize authentication requirements
- Need to decide on monitoring solution
- Need to add comprehensive test coverage for new features
- Need to add detailed documentation for new features

## Documentation
- [ ] Add easy-to-follow documentation to `README.md`
  - [ ] Provide the simplest command to run the application at the top
  - [ ] Briefly explain core concepts (config, tasks)
  - [ ] Link to detailed documentation in the `docs/` folder for advanced users