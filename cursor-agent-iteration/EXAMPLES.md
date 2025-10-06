# Cursor Agent Iteration System - Examples

This document provides real-world examples of how to use the Cursor Agent Iteration System.

## 🚀 Installation Examples

### Basic Installation
```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/your-repo/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash

# Initialize the system
make iterate-init

# Start iterating
make iterate
```

### Installation with Custom Model
```bash
# Install with specific model
MODEL="gpt-4o" make iterate-init

# Run iterations with specific model
MODEL="gpt-4o" make iterate
```

## 📋 Task Management Examples

### Adding New Tasks

**Add Authentication Tasks:**
```bash
make tasks-update PROMPT="Add comprehensive authentication tasks: OAuth2 integration, JWT token management, user session handling, and security tests. Include acceptance criteria for OAuth2 providers (Google, GitHub), JWT validation, session storage, and security scanning."
```

**Add API Development Tasks:**
```bash
make tasks-update PROMPT="Add GraphQL API tasks: schema design, resolvers implementation, authentication middleware, rate limiting, and comprehensive testing. Include tasks for query optimization, error handling, and API documentation generation."
```

**Add Database Tasks:**
```bash
make tasks-update PROMPT="Add database optimization tasks: query performance analysis, indexing strategy, connection pooling, migration scripts, and backup procedures. Include acceptance criteria for query execution time, connection limits, and data integrity."
```

### Refining Existing Tasks

**Update Task Priority:**
```bash
make tasks-update PROMPT="Reorder tasks.md to prioritize security-related tasks first, then performance optimization, then feature development. Add context about why security is the highest priority."
```

**Add More Detail to Tasks:**
```bash
make tasks-update PROMPT="Update the 'Add logging' task to include structured logging with correlation IDs, log aggregation setup, and monitoring integration. Add acceptance criteria for log format consistency and searchability."
```

**Merge Similar Tasks:**
```bash
make tasks-update PROMPT="Combine the 'Add logging' and 'Add monitoring' tasks into a single 'Observability implementation' task with comprehensive acceptance criteria for both logging and monitoring."
```

## 🔄 Iteration Examples

### Standard Iteration
```bash
# Run the next task in the backlog
make iterate
```

### Custom Iteration Focus

**Work on Security Tasks:**
```bash
make iterate-custom PROMPT="Find and work on the next security-related task from tasks.md. Focus on implementing authentication, authorization, or security scanning."
```

**Work on Database Tasks:**
```bash
make iterate-custom PROMPT="Select and implement the next database-related task. This could include schema changes, query optimization, or data migration."
```

**Work on API Tasks:**
```bash
make iterate-custom PROMPT="Find and work on the next API endpoint task. Focus on implementing REST or GraphQL endpoints with proper validation and error handling."
```

**Work on Testing Tasks:**
```bash
make iterate-custom PROMPT="Select and work on the next testing-related task. This could include unit tests, integration tests, or E2E tests."
```

### Specific Component Focus

**Frontend Tasks:**
```bash
make iterate-custom PROMPT="Work on the next frontend/UI task from tasks.md. Focus on React components, TypeScript types, or user interface improvements."
```

**Backend Tasks:**
```bash
make iterate-custom PROMPT="Work on the next backend task from tasks.md. Focus on Python services, API endpoints, or data processing."
```

**DevOps Tasks:**
```bash
make iterate-custom PROMPT="Work on the next DevOps/infrastructure task. Focus on CI/CD, deployment, monitoring, or configuration management."
```

## 🔧 Repository-Specific Examples

### Python-Only Repository
```bash
# Regenerate for Python-only
make iterate-custom PROMPT="Regenerate prompts/iterate.md and tasks.md for a Python-only repository. Remove TypeScript quality gates and focus on Python-specific tooling (mypy, pytest, black, ruff, hypothesis)."
```

### TypeScript-Only Repository
```bash
# Regenerate for TypeScript-only
make iterate-custom PROMPT="Regenerate prompts/iterate.md and tasks.md for a TypeScript-only repository. Remove Python quality gates and focus on TypeScript-specific tooling (tsc, eslint, jest, vitest, zod)."
```

### Full-Stack Repository
```bash
# Regenerate for full-stack
make iterate-custom PROMPT="Regenerate prompts/iterate.md and tasks.md for a full-stack repository with Python backend and React frontend. Include quality gates for both stacks and integration testing between them."
```

## 🚨 Troubleshooting Examples

### Diagnose Quality Gate Failures
```bash
make iterate-custom PROMPT="Diagnose why the quality gates are failing in the current iteration. Check Python (mypy, ruff, black, pytest) and TypeScript (tsc, eslint, jest) outputs. Provide specific error messages and suggested fixes."
```

### Analyze Repository Structure
```bash
make iterate-custom PROMPT="Analyze the current repository structure and explain what was detected. Include information about detected languages, frameworks, package managers, and folder layouts. Suggest improvements to the task list based on the analysis."
```

### Get Task Recommendations
```bash
make iterate-custom PROMPT="Review the current tasks.md and suggest improvements or additional tasks. Consider the repository structure, existing code quality, and common development patterns for this type of project."
```

## 📈 Progress Tracking Examples

### Review Progress
```bash
# Check what's been completed
make iterate-custom PROMPT="Review progress.md and provide a summary of completed tasks, current status, and next steps. Identify any blockers or areas that need attention."
```

### Update Documentation
```bash
# Update architecture documentation
make iterate-custom PROMPT="Update architecture.md based on recent changes. Include new components, updated data flow, and any architectural decisions that were made."
```

### Generate Reports
```bash
# Generate progress report
make iterate-custom PROMPT="Generate a comprehensive progress report including: completed tasks, test coverage improvements, quality gate pass rates, and recommendations for next iteration cycle."
```

## 🎯 Advanced Usage Examples

### Bulk Task Updates
```bash
# Update multiple tasks based on new requirements
make tasks-update PROMPT="Review all tasks in tasks.md and update them based on our new requirement to support multi-tenancy. Add context about tenant isolation, update acceptance criteria, and add new tasks for tenant management, data segregation, and tenant-specific configurations."
```

### Task Template Customization
```bash
# Add custom task templates
make tasks-update PROMPT="Add a new task template to tasks.md for 'Performance Optimization' tasks. Include standard acceptance criteria for performance testing, benchmarking, monitoring, and optimization techniques."
```

### Quality Gate Updates
```bash
# Update quality gates
make iterate-custom PROMPT="Update the quality gates in prompts/iterate.md to include security scanning with bandit for Python and npm audit for TypeScript. Also add code complexity analysis and dependency vulnerability scanning."
```

## 🔄 Complete Workflow Example

```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/your-repo/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash

# 2. Initialize for your repository
make iterate-init

# 3. Add specific tasks for your project
make tasks-update PROMPT="Add tasks for implementing a real-time chat system with WebSockets, including: WebSocket server setup, client-side connection handling, message broadcasting, user presence tracking, and comprehensive testing."

# 4. Start working on tasks
make iterate

# 5. Continue with custom focus
make iterate-custom PROMPT="Work on the next WebSocket-related task"

# 6. Add more tasks as needed
make tasks-update PROMPT="Add tasks for implementing message persistence, user authentication for WebSocket connections, and rate limiting."

# 7. Continue iterating
make iterate

# 8. Review progress
make iterate-custom PROMPT="Generate a progress report for the chat system implementation, including completed features, remaining tasks, and any blockers."
```

## 🎨 Customization Examples

### Custom Quality Gates
```bash
# Add custom quality gates
make iterate-custom PROMPT="Update the quality gates to include custom linting rules, security scanning with custom tools, and performance benchmarking with specific thresholds for this project."
```

### Custom Task Categories
```bash
# Add custom task categories
make tasks-update PROMPT="Add a new category of tasks called 'AI/ML Integration' with tasks for model deployment, inference optimization, and data pipeline integration. Include acceptance criteria specific to machine learning workflows."
```

### Custom Documentation
```bash
# Customize documentation generation
make iterate-custom PROMPT="Update the documentation generation to include API documentation with OpenAPI/Swagger, user guides with screenshots, and technical documentation with architecture diagrams."
```

---

These examples should give you a comprehensive understanding of how to use the Cursor Agent Iteration System effectively. Start with the basic examples and gradually move to more advanced usage as you become familiar with the system.
