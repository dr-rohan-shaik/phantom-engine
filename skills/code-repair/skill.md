---
name: code-repair
description: Automated code modification, refactoring, and bug fixing
---

# Code Repair Skill

Provides automated code repair and refactoring capabilities for Phantom Engine.

## Capabilities

1. **Bug Fix Patterns**
   - Null check insertion
   - Boundary condition fixes
   - Resource cleanup (try/finally, context managers)
   - Exception handling improvement
   - Race condition fixes (locks, atomic operations)
   - Memory leak fixes (reference cleanup, weak references)

2. **Refactoring Operations**
   - Extract method/function
   - Extract class/module
   - Inline method
   - Rename symbol
   - Move method/field
   - Replace conditional with polymorphism
   - Introduce parameter object
   - Replace magic numbers with constants

3. **Code Modernization**
   - Update deprecated APIs
   - Migrate to new language features
   - Convert callbacks to async/await
   - Replace legacy patterns with modern equivalents

4. **Security Fixes**
   - Input sanitization
   - Parameterized queries
   - Output encoding
   - Secure header addition
   - Dependency updates for CVEs

## Safety Guarantees

- All changes wrapped in git checkpoints
- Tests run before and after each change
- Rollback on test failure
- Minimal change principle
- Preserve formatting and style

## Usage

```python
from skills.code_repair import CodeRepairer

repairer = CodeRepairer(repo_path)
result = repairer.fix_issue(finding)
```

## Output

- Modified source files
- Updated tests
- `.phantom/changelog.md` - Change log
- Git commits with descriptive messages