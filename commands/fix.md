---
name: phantom:fix
description: Find and repair identified bugs in the repository
arguments:
  - name: target
    description: Specific file, directory, or issue to fix
    required: false
  - name: auto-test
    description: Automatically run tests after fixes
    required: false
---

# /phantom:fix

Find and repair bugs in the repository.

## Usage

```
/phantom:fix
/phantom:fix --target "src/api/users.py"
/phantom:fix --auto-test
```

## What It Does

1. **Investigate** - Runs static analysis and checks for bug patterns
2. **Prioritize** - Ranks issues by severity and impact
3. **Fix** - Implements minimal, targeted fixes
4. **Test** - Runs regression tests for each fix
5. **Verify** - Confirms fixes resolve issues without regressions

## Output

- Modified source files
- New/updated test files
- `.phantom/changelog.md` - Change log
- `.phantom/findings.md` - Updated findings with fix status