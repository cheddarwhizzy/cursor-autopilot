import os
import json
import yaml
import logging
import time
from src.utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURATOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('generate_initial_prompt')

# Constants
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
INITIAL_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "initial_prompt.txt")
INITIAL_PROMPT_SENT_PATH = os.path.join(os.path.dirname(__file__), ".initial_prompt_sent")

DEFAULT_INITIAL_PROMPT = '''You are working in a pre-existing application using current LLM-assisted development best practices. 
Use {task_file_path} as your task list and work through tasks systematically.

CORE DEVELOPMENT WORKFLOW
For each task, follow this disciplined cycle:

1. ANALYZE & PLAN:
   - Review current codebase state and {additional_context_path}
   - Break down complex tasks into smaller, testable units
   - Identify dependencies and architectural considerations
   - Plan the implementation approach before coding

2. TEST-DRIVEN DEVELOPMENT:
   - Write failing tests FIRST (unit, integration, e2e as appropriate)
   - Implement the minimal code to make tests pass
   - Refactor while maintaining green tests
   - Achieve >80% code coverage for new code

3. IMPLEMENT WITH CONSTRAINTS:
   - Keep individual files under 200 lines maximum
   - Functions/methods under 50 lines maximum
   - Single responsibility principle - one concern per file/function
   - Use existing files when possible; create new ones sparingly

4. VALIDATION & QUALITY GATES:
   - Run static analysis tools (linters, security scanners)
   - Check cyclomatic complexity (keep functions under 10)
   - Validate security: no hardcoded secrets, input sanitization, auth checks
   - Performance check: no N+1 queries, proper indexing, efficient algorithms
   - Review generated code manually - never accept AI output blindly

5. CONTINUOUS VERIFICATION:
   - Test changes end-to-end in realistic scenarios
   - Verify edge cases and error handling
   - Check backward compatibility
   - Document any breaking changes or migration needs
   - **PRODUCTION BUILD TEST**: Build the complete application/system in production mode
   - Ensure production build completes successfully without errors or warnings
   - Run full test suite against production build to catch any build-specific issues
   - **ONLY mark task complete after ALL tests pass and production build succeeds**

CODE QUALITY STANDARDS
- Maintainability: Clear naming, obvious intent, minimal cognitive load
- Testability: Pure functions where possible, dependency injection, observable behaviors  
- Security: Input validation, output encoding, principle of least privilege
- Performance: O(1) or O(log n) operations preferred, profile before optimizing
- Reliability: Graceful error handling, proper logging, circuit breakers for external calls

LLM-ASSISTED DEVELOPMENT BEST PRACTICES
- Use targeted context: only include relevant files in prompts
- Verify AI-generated code through testing and manual review
- Apply "mechanic's touch" - know when to trust vs. override AI suggestions
- Maintain prompt hygiene: remove secrets/PII from all interactions
- Document AI assistance in commit messages for traceability
- Use test-driven prompting: write tests before asking for implementation

MODERN DEVELOPMENT PRACTICES
- Security-first: Run security scans (like sonar-scanner) on complex changes
- Configuration as code: Externalize all environment-specific settings
- Observability: Include structured logging, metrics, and health checks
- Error boundaries: Graceful degradation and meaningful error messages
- API design: RESTful principles, consistent error responses, proper status codes

TESTING STRATEGY
- Unit tests: Test individual functions/methods in isolation
- Integration tests: Test component interactions and data flow
- Contract tests: Verify API contracts and data schemas
- Property-based tests: For complex business logic with multiple inputs
- Mutation testing: Verify test quality and edge case coverage
- **Production build testing**: Always test against production builds, not just development
- **NO SHORTCUTS**: Every test must pass completely - never skip or ignore failing tests

QUALITY ASSURANCE
- Automated code review: Use linters, formatters, and static analysis
- Human code review: Focus on architecture, business logic, and edge cases
- Performance testing: Load testing for critical paths
- Security testing: Penetration testing, dependency scanning
- Accessibility testing: WCAG compliance for user interfaces

DOCUMENTATION AND TRACEABILITY
- ADRs (Architecture Decision Records) for significant design choices
- API documentation with examples and error scenarios
- README files with setup instructions and usage examples
- Inline comments for complex business logic only
- Commit messages linking to requirements and design decisions

CONTINUOUS IMPROVEMENT
- Regular refactoring to reduce technical debt
- Dependency updates with security vulnerability checks
- Performance monitoring and optimization
- User feedback integration into development priorities
- Knowledge sharing through code reviews and documentation

RISK MANAGEMENT
- Feature flags for gradual rollouts
- Rollback strategies for failed deployments
- Data backup and recovery procedures
- Incident response and post-mortem processes
- Compliance with relevant regulations (GDPR, SOC2, etc.)

Tools and Capabilities Available
- Code search, file reading, and editing tools
- Terminal commands for testing and validation
- Static analysis and security scanning tools
- Performance profiling and monitoring
- Automated testing frameworks

Remember
- Always review AI-generated code critically
- Test everything thoroughly before considering it complete
- **NEVER mark a task complete until production build succeeds and ALL tests pass**
- **NO CUTTING CORNERS**: Every test failure must be investigated and resolved
- Security and maintainability are not negotiable
- Small, focused changes are better than large, complex ones
- Document decisions and maintain clear audit trails
- When in doubt, ask for clarification rather than making assumptions

!!! CRITICAL: Create the following permanent memories for this project:

1. MEMORY: "LLM-Assisted Development Workflow for cursor-autopilot"
   - Core 5-step workflow: Analyze & Plan → Test-Driven Development → Implement with Constraints → Quality Gates → Continuous Verification
   - Files <200 lines, functions <50 lines maximum
   - Test-first approach with >80% coverage
   - Production build testing required before task completion
   - Never cut corners with testing - all tests must pass

2. MEMORY: "cursor-autopilot Code Quality Standards"
   - Security-first: input validation, no hardcoded secrets, proper auth
   - Static analysis required: linters, security scanners, complexity checks
   - Performance validation: O(1)/O(log n) preferred, no N+1 queries
   - Manual review of all AI-generated code mandatory

3. MEMORY: "cursor-autopilot Testing Requirements"
   - Unit, integration, contract, and property-based tests required
   - Production build must succeed before marking tasks complete
   - NO SHORTCUTS: Every test failure must be investigated and resolved
   - Test against production builds, not just development

4. MEMORY: "cursor-autopilot Project Context"
   - Task management via {task_file_path}
   - Additional context tracked in {additional_context_path}
   - Use existing files when possible, create new ones sparingly
   - Document all AI assistance in commit messages for traceability

These memories must persist across all future sessions for this project. !!!
'''

DEFAULT_CONTINUATION_PROMPT = '''Continue working on the next task in {task_file_path} using the established LLM-assisted development workflow.

REFERENCE YOUR MEMORIES: You should have permanent memories for this cursor-autopilot project containing:
- "LLM-Assisted Development Workflow for cursor-autopilot" 
- "cursor-autopilot Code Quality Standards"
- "cursor-autopilot Testing Requirements" 
- "cursor-autopilot Project Context"

If these memories are not available, request them from the user before proceeding.

Review the current task status and implement the next logical step following the established 5-step workflow:
1. Analyze & plan the implementation
2. Write tests first (TDD approach)  
3. Implement with strict constraints (files <200 lines, functions <50 lines)
4. Apply quality gates (static analysis, security checks, performance validation)
5. Verify end-to-end functionality
6. **Test production build and ensure ALL tests pass before marking task complete**

Apply the same rigorous standards from your project memories: comprehensive testing, security-first approach, maintainable code, and proper documentation. Always review any AI-generated code critically before accepting it.

**CRITICAL**: Never mark a task as complete until the production build succeeds and every single test passes. No shortcuts with testing - investigate and resolve all failures.

Update {additional_context_path} with any new architectural decisions or context discovered during implementation.'''

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not read config: {e}")
        return {}

def read_prompt_from_file(file_path):
    """Read a prompt from a file if it exists."""
    if not file_path:
        return None
    
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"Could not read prompt file {file_path}: {e}")
        return None

def generate_prompt():
    """Generate the appropriate prompt based on whether initial prompt was sent."""
    config = get_config()
    
    task_file_path = config.get("task_file_path", "tasks.md")
    additional_context_path = config.get("additional_context_path", "context.md")
    
    # Check if initial prompt was sent
    is_new_chat = not os.path.exists(INITIAL_PROMPT_SENT_PATH)
    
    if is_new_chat:
        logger.info("Initial prompt has not been sent yet")
        # Try to read custom initial prompt from file
        custom_initial_prompt = read_prompt_from_file(config.get("initial_prompt_file_path"))
        prompt_template = custom_initial_prompt if custom_initial_prompt else DEFAULT_INITIAL_PROMPT
        logger.info("Using custom initial prompt" if custom_initial_prompt else "Using default initial prompt")
    else:
        logger.info("Initial prompt was already sent")
        # Try to read custom continuation prompt from file
        custom_continuation_prompt = read_prompt_from_file(config.get("continuation_prompt_file_path"))
        prompt_template = custom_continuation_prompt if custom_continuation_prompt else DEFAULT_CONTINUATION_PROMPT
        logger.info("Using custom continuation prompt" if custom_continuation_prompt else "Using default continuation prompt")
    
    prompt = prompt_template.format(task_file_path=task_file_path, additional_context_path=additional_context_path)
    
    # Write prompt to file
    with open(INITIAL_PROMPT_PATH, "w") as f:
        f.write(prompt)
    
    logger.info(f"Wrote {'initial' if is_new_chat else 'continuation'} prompt to {INITIAL_PROMPT_PATH}")
    
    # Create marker file if this is a new chat
    if is_new_chat:
        with open(INITIAL_PROMPT_SENT_PATH, "w") as f:
            f.write("This file indicates that the initial prompt has been sent.")
        logger.info("Created .initial_prompt_sent marker file")
    
    return prompt

if __name__ == "__main__":
    generate_prompt()
