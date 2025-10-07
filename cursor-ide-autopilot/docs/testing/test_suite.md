# Test Suite Documentation

## Overview

The Cursor Autopilot test suite includes comprehensive tests for all major components and features. This document explains the different types of tests and how to run them.

## Test Categories

### 1. Unit Tests

Located in:
- `tests/test_cli.py`: Command-line interface tests
- `tests/test_keystrokes.py`: Keystroke handling tests
- `tests/test_config.py`: Configuration validation tests

These tests verify individual components in isolation.

### 2. Integration Tests

Located in `tests/test_integration.py`, covering:
- Performance testing for simultaneous automation
- Security testing for API endpoints
- Error handling and edge cases
- Complete workflow testing
- Resource cleanup
- Logging and monitoring

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_integration.py

# Run specific test function
pytest tests/test_integration.py::test_simultaneous_automation_performance
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=.

# Generate HTML coverage report
pytest --cov=. --cov-report=html
```

### Performance Testing

```bash
# Run performance tests with timing
pytest tests/test_integration.py::test_simultaneous_automation_performance -v
```

## Test Descriptions

### CLI Tests (`test_cli.py`)
- Configuration loading and validation
- Command-line argument parsing
- Config merging and precedence
- Error handling for invalid inputs

### Keystroke Tests (`test_keystrokes.py`)
- Key mapping for different platforms
- Single keystroke sending
- Keystroke sequences
- Window activation
- Error handling for invalid keys

### Configuration Tests (`test_config.py`)
- YAML configuration loading
- Platform-specific validation
- Vision conditions configuration
- Slack integration configuration
- OpenAI configuration

### Integration Tests (`test_integration.py`)
- Performance testing for simultaneous automation
  - Single platform performance
  - Multi-platform performance
  - Timing constraints
- Security testing
  - Rate limiting
  - Authentication
  - Input validation
- Error handling
  - Invalid inputs
  - Edge cases
  - Configuration errors
- Complete workflow testing
  - Initialization
  - Task execution
  - Vision conditions
- Resource cleanup
  - File handles
  - Thread management
- Logging and monitoring
  - Debug logging
  - Error logging
  - Performance monitoring

## Best Practices

1. **Writing Tests**
   - Follow AAA pattern (Arrange, Act, Assert)
   - Use descriptive test names
   - Include docstrings explaining test purpose
   - Test both success and failure cases
   - Include edge cases and boundary conditions

2. **Running Tests**
   - Run tests before committing changes
   - Check coverage reports regularly
   - Monitor test execution time
   - Fix failing tests immediately

3. **Maintenance**
   - Keep tests up to date with code changes
   - Remove obsolete tests
   - Add tests for new features
   - Document test requirements

## Troubleshooting

1. **Common Issues**
   - Test timing out: Adjust timeouts in performance tests
   - Platform-specific failures: Use platform-specific test cases
   - Resource cleanup failures: Check thread and file handle management

2. **Debugging**
   - Use `-v` flag for verbose output
   - Add print statements in failing tests
   - Check test logs
   - Review coverage reports

3. **Performance Issues**
   - Monitor test execution time
   - Optimize slow tests
   - Use appropriate timeouts
   - Consider parallel test execution

## Continuous Integration

The test suite is integrated with CI/CD pipelines:
- Automatic test execution on pull requests
- Coverage reporting
- Performance monitoring
- Security scanning

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/) 