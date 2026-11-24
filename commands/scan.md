---
name: phantom:scan
description: Analyze the repository structure, languages, frameworks, and dependencies
arguments:
  - name: deep
    description: Perform deep analysis including security scan
    required: false
---

# /phantom:scan

Analyze the repository and create a comprehensive architecture report.

## Usage

```
/phantom:scan
/phantom:scan --deep
```

## What It Does

1. **Repository Structure** - Maps directories, files, and entry points
2. **Language Detection** - Identifies all programming languages used
3. **Framework Detection** - Detects frameworks (React, Django, FastAPI, etc.)
4. **Dependency Analysis** - Lists all package managers and dependencies
5. **Git Status** - Shows current branch, changes, and history
6. **Architecture Patterns** - Identifies architectural patterns used
7. **Security Scan** (with --deep) - Runs security auditing tools

## Output

- `.phantom/scan-report.md` - Detailed analysis report
- `.phantom/architecture.md` - Architecture documentation
- Updates state with detected technologies