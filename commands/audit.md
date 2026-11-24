---
name: phantom:audit
description: Perform code quality and security audits
arguments:
  - name: security-only
    description: Only run security audit
    required: false
  - name: quality-only
    description: Only run code quality audit
    required: false
---

# /phantom:audit

Perform comprehensive code quality and security audits.

## Usage

```
/phantom:audit
/phantom:audit --security-only
/phantom:audit --quality-only
```

## What It Does

### Security Audit
- OWASP Top 10 vulnerability scanning
- Dependency vulnerability checking (npm audit, pip-audit, cargo audit)
- Secret exposure detection
- Permission and configuration review

### Code Quality Audit
- Complexity analysis (cyclomatic, cognitive)
- Code duplication detection
- Coding standards compliance
- Test coverage analysis
- Dead code detection

## Output

- `.phantom/audit-report.md` - Combined audit report
- `.phantom/security-findings.md` - Security-specific findings
- `.phantom/quality-findings.md` - Quality-specific findings
- Severity-ranked issue list