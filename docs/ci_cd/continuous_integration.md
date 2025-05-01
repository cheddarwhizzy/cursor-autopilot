# Continuous Integration and Deployment

## Overview

The Cursor Autopilot project uses GitHub Actions for continuous integration and deployment. This document explains the CI/CD pipeline and how to work with it.

## CI Pipeline

The CI pipeline runs on every push to the main branch and on pull requests. It includes the following jobs:

### 1. Testing

Runs on multiple platforms and Python versions:
- Operating Systems: Ubuntu, macOS, Windows
- Python Versions: 3.8, 3.9, 3.10

Tasks:
- Install dependencies
- Run test suite
- Generate coverage report
- Upload coverage to Codecov
- Verify minimum coverage (80%)

### 2. Linting

Runs on Ubuntu:
- Check code style with flake8
- Format check with black

### 3. Security

Runs on Ubuntu:
- Static code analysis with bandit
- Dependency vulnerability check with safety

### 4. Performance

Runs on Ubuntu:
- Run performance benchmarks
- Monitor execution times

## Configuration

The CI pipeline is configured in `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    # ... test configuration ...
  lint:
    # ... lint configuration ...
  security:
    # ... security configuration ...
  performance:
    # ... performance configuration ...
```

## Local Development

### Running CI Checks Locally

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest --cov=. --cov-report=html
```

3. Run linters:
```bash
flake8 .
black . --check
```

4. Run security checks:
```bash
bandit -r .
safety check
```

5. Run performance tests:
```bash
pytest tests/test_integration.py::test_simultaneous_automation_performance --benchmark-only
```

### Pre-commit Hooks

To ensure code quality before committing:

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Install hooks:
```bash
pre-commit install
```

3. Run hooks manually:
```bash
pre-commit run --all-files
```

## Best Practices

1. **Before Pushing**
   - Run all tests locally
   - Fix any linting issues
   - Check security warnings
   - Verify performance benchmarks

2. **Pull Requests**
   - Ensure all CI checks pass
   - Address any code review comments
   - Update documentation if needed
   - Keep commits focused and atomic

3. **Main Branch**
   - Keep main branch stable
   - Use feature branches for development
   - Squash and merge PRs
   - Follow semantic versioning

## Troubleshooting

1. **CI Failures**
   - Check the GitHub Actions logs
   - Verify local tests pass
   - Update dependencies if needed
   - Check for platform-specific issues

2. **Coverage Issues**
   - Add missing test cases
   - Update coverage configuration
   - Exclude non-testable code
   - Document exclusions

3. **Performance Regressions**
   - Check benchmark results
   - Profile slow operations
   - Optimize critical paths
   - Update performance thresholds

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/) 