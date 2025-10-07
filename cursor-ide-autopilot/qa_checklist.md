# Quality Assurance Checklist

This file tracks quality gates and validation criteria.

## Code Quality Gates
- [ ] **Linting**: All code passes linting rules
- [ ] **Formatting**: Code is properly formatted
- [ ] **Type Checking**: All types are properly defined
- [ ] **Testing**: Adequate test coverage
- [ ] **Security**: No security vulnerabilities
- [ ] **Documentation**: Code is properly documented

## Technology-Specific Gates
- **Python**: ruff, black, mypy, pytest
- **TypeScript/JavaScript**: tsc, eslint, jest/vitest
- **Go**: go vet, golangci-lint, go test
- **Rust**: cargo clippy, cargo test, cargo fmt
- **Java**: mvn spotbugs, mvn checkstyle, mvn test
- **Infrastructure**: terraform validate, ansible-lint, dockerfile-lint

---
*This file is automatically updated by the iteration system*
