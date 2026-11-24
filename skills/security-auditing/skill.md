---
name: security-auditing
description: Comprehensive security vulnerability detection and remediation
---

# Security Auditing Skill

Provides comprehensive security auditing capabilities for Phantom Engine.

## Capabilities

1. **Vulnerability Scanning**
   - OWASP Top 10 coverage
   - SAST (Static Application Security Testing)
   - DAST (Dynamic Application Security Testing) integration
   - SCA (Software Composition Analysis)
   - Container/image scanning

2. **Dependency Auditing**
   - CVE database checking (NVD, GitHub Advisory, OSV)
   - License compliance verification
   - Supply chain risk assessment
   - Typosquatting detection
   - Malicious package detection

3. **Secret Detection**
   - API keys, tokens, passwords
   - Database credentials
   - Cloud provider keys (AWS, GCP, Azure)
   - SSH keys and certificates
   - Custom pattern matching

4. **Configuration Security**
   - Insecure defaults detection
   - Excessive permissions
   - Exposed ports/services
   - Missing security headers
   - Weak encryption settings

5. **Code Security Patterns**
   - SQL injection detection
   - XSS vulnerability detection
   - Command injection detection
   - Path traversal detection
   - Insecure deserialization
   - XXE vulnerability detection
   - SSRF vulnerability detection

## Tools Integrated

- **Python**: bandit, safety, pip-audit, semgrep
- **JavaScript/TypeScript**: npm audit, eslint-plugin-security, semgrep
- **Go**: gosec, govulncheck
- **Rust**: cargo audit, cargo deny
- **Java**: spotbugs, dependency-check
- **Container**: trivy, grype, syft
- **General**: semgrep, trufflehog, git-secrets

## Output

- `.phantom/security-report.md` - Human-readable report
- `.phantom/security-findings.json` - Structured findings
- SARIF format for CI integration
- Remediation guidance per finding

## Severity Levels

- **CRITICAL** - Active exploitation possible, immediate action required
- **HIGH** - Significant risk, fix before deployment
- **MEDIUM** - Moderate risk, fix in next sprint
- **LOW** - Minor risk, fix when convenient
- **INFO** - Informational, no immediate action needed