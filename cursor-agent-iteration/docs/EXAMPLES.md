# Cursor Agent Iteration System - Examples

This document provides real-world examples of how to use the Cursor Agent Iteration System.

## 🚀 Installation Examples

### Basic Installation
```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash

# Initialize the system
cursor-iter iterate-init

# Start iterating
cursor-iter iterate
```

### Installation with Custom Model
```bash
# Install with specific model
cursor-iter iterate-init --model gpt-4o

# Run iterations with specific model
MODEL="gpt-4o" cursor-iter iterate
```

## 📋 Task Management Examples

### Adding New Tasks

**Add Authentication Tasks:**
```bash
cursor-iter add-feature --prompt "Add comprehensive authentication tasks: OAuth2 integration, JWT token management, user session handling, and security tests. Include acceptance criteria for OAuth2 providers (Google, GitHub), JWT validation, session storage, and security scanning."
```

**Add API Development Tasks:**
```bash
cursor-iter add-feature --prompt "Add GraphQL API tasks: schema design, resolvers implementation, authentication middleware, rate limiting, and comprehensive testing. Include tasks for query optimization, error handling, and API documentation generation."
```

**Add Database Tasks:**
```bash
cursor-iter add-feature --prompt "Add database optimization tasks: query performance analysis, indexing strategy, connection pooling, migration scripts, and backup procedures. Include acceptance criteria for query execution time, connection limits, and data integrity."
```

### Refining Existing Tasks

**Update Task Priority:**
```bash
cursor-iter add-feature --prompt "Reorder tasks.md to prioritize security-related tasks first, then performance optimization, then feature development. Add context about why security is the highest priority."
```

**Add More Detail to Tasks:**
```bash
cursor-iter add-feature --prompt "Update the 'Add logging' task to include structured logging with correlation IDs, log aggregation setup, and monitoring integration. Add acceptance criteria for log format consistency and searchability."
```

**Merge Similar Tasks:**
```bash
cursor-iter add-feature --prompt "Combine the 'Add logging' and 'Add monitoring' tasks into a single 'Observability implementation' task with comprehensive acceptance criteria for both logging and monitoring."
```

## 🔄 Iteration Examples

### Standard Iteration
```bash
# Run the next task in the backlog
cursor-iter iterate
```

### Custom Iteration Focus

**Work on Security Tasks:**
```bash
cursor-iter iterate
```

**Work on Database Tasks:**
```bash
cursor-iter iterate
```

**Work on API Tasks:**
```bash
cursor-iter iterate
```

**Work on Testing Tasks:**
```bash
cursor-iter iterate
```

### Specific Component Focus

**Frontend Tasks:**
```bash
cursor-iter iterate
```

**Backend Tasks:**
```bash
cursor-iter iterate
```

**DevOps Tasks:**
```bash
cursor-iter iterate
```

## 🔧 Repository-Specific Examples

### Python-Only Repository
```bash
# Regenerate for Python-only
cursor-iter iterate-init --model auto
```

### TypeScript-Only Repository
```bash
# Regenerate for TypeScript-only
cursor-iter iterate-init --model auto
```

### Full-Stack Repository
```bash
# Regenerate for full-stack
cursor-iter iterate-init --model auto
```

## 🚨 Troubleshooting Examples

### Diagnose Quality Gate Failures
```bash
cursor-iter iterate
```

### Analyze Repository Structure
```bash
cursor-iter task-status
```

### Get Task Recommendations
```bash
cursor-iter add-feature --prompt "Review the current tasks.md and suggest improvements or additional tasks. Consider the repository structure, existing code quality, and common development patterns for this type of project."
```

## 📈 Progress Tracking Examples

### Review Progress
```bash
# Check what's been completed
cursor-iter task-status
```

### Update Documentation
```bash
# Update architecture documentation
cursor-iter iterate
```

### Generate Reports
```bash
# Generate progress report
cursor-iter task-status
```

## 🎯 Advanced Usage Examples

### Bulk Task Updates
```bash
# Update multiple tasks based on new requirements
cursor-iter add-feature --prompt "Review all tasks in tasks.md and update them based on our new requirement to support multi-tenancy. Add context about tenant isolation, update acceptance criteria, and add new tasks for tenant management, data segregation, and tenant-specific configurations."
```

### Task Template Customization
```bash
# Add custom task templates
cursor-iter add-feature --prompt "Add a new task template to tasks.md for 'Performance Optimization' tasks. Include standard acceptance criteria for performance testing, benchmarking, monitoring, and optimization techniques."
```

### Quality Gate Updates
```bash
# Update quality gates
cursor-iter iterate-init --model auto
```

## 🔄 Complete Workflow Example

```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

# 2. Initialize for your repository
cursor-iter iterate-init

# 3. Add specific tasks for your project
cursor-iter add-feature --prompt "Add tasks for implementing a real-time chat system with WebSockets, including: WebSocket server setup, client-side connection handling, message broadcasting, user presence tracking, and comprehensive testing."

# 4. Start working on tasks
cursor-iter iterate

# 5. Continue with custom focus
cursor-iter iterate

# 6. Add more tasks as needed
cursor-iter add-feature --prompt "Add tasks for implementing message persistence, user authentication for WebSocket connections, and rate limiting."

# 7. Continue iterating
cursor-iter iterate

# 8. Review progress
cursor-iter task-status
```

## 🎨 Customization Examples

### Custom Quality Gates
```bash
# Add custom quality gates
cursor-iter iterate-init --model auto
```

### Custom Task Categories
```bash
# Add custom task categories
cursor-iter add-feature --prompt "Add a new category of tasks called 'AI/ML Integration' with tasks for model deployment, inference optimization, and data pipeline integration. Include acceptance criteria specific to machine learning workflows."
```

### Custom Documentation
```bash
# Customize documentation generation
cursor-iter iterate
```

---

These examples should give you a comprehensive understanding of how to use the Cursor Agent Iteration System effectively. Start with the basic examples and gradually move to more advanced usage as you become familiar with the system.
