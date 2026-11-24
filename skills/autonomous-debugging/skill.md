---
name: autonomous-debugging
description: Automated bug detection, root-cause analysis, and reproduction
---

# Autonomous Debugging Skill

Provides automated debugging capabilities for Phantom Engine.

## Capabilities

1. **Bug Pattern Detection**
   - Null/undefined reference detection
   - Race condition identification
   - Memory leak patterns
   - Resource leak detection
   - Infinite loop detection
   - Off-by-one errors
   - Type mismatch detection

2. **Static Analysis Integration**
   - Runs linters (ruff, eslint, golangci-lint, clippy)
   - Runs type checkers (mypy, tsc, pyright)
   - Runs security scanners (bandit, safety, npm audit)
   - Custom rule engine for project-specific patterns

3. **Root Cause Analysis**
   - Stack trace analysis
   - Git bisect integration for regression detection
   - Dependency chain tracing
   - Configuration drift detection

4. **Reproduction Generation**
   - Minimal test case generation
   - Input fuzzing for edge cases
   - Environment replication
   - Deterministic reproduction scripts

## Workflow

1. Run static analysis tools
2. Analyze test failures
3. Correlate with recent changes
4. Generate reproduction
5. Identify root cause
6. Rank by severity and exploitability

## Output

- `.phantom/findings.md` - Structured findings
- `.phantom/reproduction/` - Reproduction scripts
- Severity rankings (CRITICAL, HIGH, MEDIUM, LOW)