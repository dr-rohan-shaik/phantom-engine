---
name: phantom:test
description: Run the verification suite including unit, integration, and E2E tests
arguments:
  - name: coverage
    description: Minimum coverage threshold (default 80)
    required: false
  - name: watch
    description: Watch mode for continuous testing
    required: false
---

# /phantom:test

Run the complete verification test suite.

## Usage

```
/phantom:test
/phantom:test --coverage 90
/phantom:test --watch
```

## What It Does

1. **Unit Tests** - Runs all unit tests with coverage
2. **Integration Tests** - Runs integration tests if configured
3. **E2E Tests** - Runs end-to-end tests if configured
4. **Linting** - Runs linters (ruff, eslint, etc.)
5. **Type Checking** - Runs type checkers (mypy, tsc, etc.)
6. **Security Tests** - Runs security-focused tests

## Output

- `.phantom/test-results.json` - Structured test results
- Coverage report
- Pass/fail summary