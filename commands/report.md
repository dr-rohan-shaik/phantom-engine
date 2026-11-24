---
name: phantom:report
description: Generate a comprehensive engineering report
arguments:
  - name: format
    description: Output format (markdown, json, html)
    required: false
---

# /phantom:report

Generate a comprehensive engineering report from the current or completed session.

## Usage

```
/phantom:report
/phantom:report --format json
/phantom:report --format html
```

## What It Does

Compiles all session data into a structured report including:

- Original task and repository analysis
- Problems discovered and fixes implemented
- Files modified, created, deleted
- Dependencies changed
- Tests executed and results
- Security findings
- Git commits and PR status
- Deployment status and URL
- Remaining issues
- Completion status

## Output

- `.phantom/final-report.md` - Main report (markdown)
- `.phantom/final-report.json` - Structured data
- `.phantom/final-report.html` - HTML version (if requested)