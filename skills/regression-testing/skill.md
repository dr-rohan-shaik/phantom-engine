---
name: regression-testing
description: Automated regression test generation, execution, and verification
---

# Regression Testing Skill

Provides comprehensive regression testing capabilities for Phantom Engine.

## Capabilities

1. **Test Generation**
   - Generates tests from bug reproductions
   - Creates parameterized test cases
   - Generates property-based tests
   - Creates integration test scenarios

2. **Test Execution**
   - Runs unit tests (pytest, jest, cargo test, go test)
   - Runs integration tests
   - Runs E2E tests (Playwright, Cypress)
   - Parallel test execution
   - Test quarantine for flaky tests

3. **Coverage Analysis**
   - Line coverage
   - Branch coverage
   - Function coverage
   - Coverage thresholds enforcement
   - Coverage regression detection

4. **Regression Detection**
   - Compares test results across runs
   - Identifies new failures
   - Tracks flaky tests
   - Bisects regressions to commits

## Workflow

1. Analyze codebase for test gaps
2. Generate missing tests (TDD approach)
3. Run full test suite
4. Verify coverage meets threshold (80% default)
5. Quarantine flaky tests
6. Report results

## Output

- `.phantom/test-results.json` - Structured test results
- `.phantom/coverage-report/` - Coverage reports
- Quarantined test list
- Test trend analysis

## Integration

Works with:
- pytest (Python)
- jest/vitest (JavaScript/TypeScript)
- cargo test (Rust)
- go test (Go)
- JUnit/TestNG (Java)
- Playwright/Cypress (E2E)