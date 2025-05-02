# Quick Start Guide

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-autopilot.git
cd cursor-autopilot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create required files:
```bash
touch tasks.md context.md
```

## Basic Setup

1. Configure your project:
```bash
# Create a basic config.yaml
cat > config.yaml << EOL
# Basic config.yaml structure expected by run.sh
platforms:
  windsurf:
    # Set the default project path (can be overridden with --project-path flag)
    project_path: "$(pwd)"
# general:
  # inactivity_delay: 300
  # send_message: true
  # debug: false
EOL
```

2. Add your first task:
```bash
# Add a task to tasks.md
cat > tasks.md << EOL
# Project Tasks

## New Feature
- [ ] Implement feature X
  - [ ] Create component
  - [ ] Add tests
  - [ ] Update documentation
EOL
```

3. Add project context:
```bash
# Add context to context.md
cat > context.md << EOL
# Project Context

## Overview
This project is a web application built with React and Node.js.

## Architecture
- Frontend: React with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL
EOL
```

## Running the Application

1. Start with the default project path (from `config.yaml`):
```bash
./run.sh
```

2. Start and override the project path:
```bash
# Use --project-path=VALUE or --project-path VALUE
./run.sh --project-path=/path/to/your/project
# OR
./run.sh --project-path /path/to/your/project
```

## Next Steps

1. **Configure Your IDE**
   - Install Cursor or Windsurf
   - Grant necessary permissions
   - Test keystroke sending

2. **Set Up Integrations**
   - Configure Slack webhook
   - Set up OpenAI API key
   - Test integrations

3. **Monitor Progress**
   - Check task completion
   - Review logs
   - Monitor performance

## Troubleshooting

1. **Common Issues**
   - IDE not responding: Check permissions
   - Tasks not progressing: Verify task format
   - Keystrokes not working: Test manually

2. **Debug Mode**
   - Enable with `--debug` flag
   - Check logs for details
   - Verify configuration

3. **Getting Help**
   - Check documentation
   - Review error messages
   - Contact support

## Best Practices

1. **Task Management**
   - Keep tasks small and focused
   - Use clear descriptions
   - Update progress regularly

2. **Configuration**
   - Use environment variables for secrets
   - Keep config.yaml in version control
   - Document changes

3. **Monitoring**
   - Check logs regularly
   - Monitor resource usage
   - Review task progress

## Additional Resources

- [Configuration Guide](./configuration/yaml_configuration.md)
- [API Documentation](./api/flask_configuration.md)
- [Automation Guide](./automation/simultaneous_automation.md)
- [Vision Integration](./vision/openai_vision.md) 