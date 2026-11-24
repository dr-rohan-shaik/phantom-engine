"""
Phantom Engine Report Generator
Generates comprehensive engineering reports from execution state.
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class EngineeringReport:
    """Comprehensive engineering report."""
    task: str = ""
    repository: str = ""
    git_branch: str = ""
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0
    iterations_completed: int = 0
    max_iterations: int = 10
    mode: str = "AUTO"
    success: bool = False
    final_phase: str = ""

    # Analysis
    repository_analysis: Dict[str, Any] = field(default_factory=dict)
    architecture_summary: str = ""
    languages_detected: List[str] = field(default_factory=list)
    frameworks_detected: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)

    # Findings
    problems_discovered: List[Dict[str, Any]] = field(default_factory=list)
    security_findings: List[Dict[str, Any]] = field(default_factory=list)
    bugs_fixed: List[Dict[str, Any]] = field(default_factory=list)
    vulnerabilities_fixed: List[Dict[str, Any]] = field(default_factory=list)

    # Changes
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    dependencies_changed: List[Dict[str, Any]] = field(default_factory=list)

    # Testing
    tests_executed: List[Dict[str, Any]] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    coverage: Dict[str, Any] = field(default_factory=dict)

    # Git
    commits: List[Dict[str, Any]] = field(default_factory=list)
    push_status: str = ""
    pr_url: str = ""
    pr_number: int = 0

    # Deployment
    deployment_url: str = ""
    deployment_status: str = "not_started"
    deployment_target: str = ""
    health_check_passed: bool = False

    # Issues
    remaining_issues: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Completion
    completion_status: str = "incomplete"
    completion_percentage: float = 0.0


class ReportGenerator:
    """Generates engineering reports from Phantom Engine state."""

    def __init__(self, phantom_dir: Optional[Path] = None):
        self.phantom_dir = phantom_dir or Path.cwd() / ".phantom"
        self.report_file = self.phantom_dir / "final-report.md"
        self.state_file = self.phantom_dir / "state.json"
        self.changelog_file = self.phantom_dir / "changelog.md"
        self.iteration_log = self.phantom_dir / "iteration-log.md"
        self.findings_file = self.phantom_dir / "findings.md"
        self.test_results_file = self.phantom_dir / "test-results.json"

    def load_state(self) -> Dict[str, Any]:
        """Load engine state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {}

    def load_iteration_log(self) -> str:
        """Load iteration log."""
        if self.iteration_log.exists():
            with open(self.iteration_log) as f:
                return f.read()
        return ""

    def load_findings(self) -> str:
        """Load findings."""
        if self.findings_file.exists():
            with open(self.findings_file) as f:
                return f.read()
        return ""

    def load_test_results(self) -> Dict[str, Any]:
        """Load test results."""
        if self.test_results_file.exists():
            with open(self.test_results_file) as f:
                return json.load(f)
        return {}

    def load_changelog(self) -> str:
        """Load changelog."""
        if self.changelog_file.exists():
            with open(self.changelog_file) as f:
                return f.read()
        return ""

    def get_git_commits(self) -> List[Dict[str, Any]]:
        """Get git commits from current session."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "--since", "1 hour ago", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
                capture_output=True,
                text=True,
                timeout=10
            )
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            return commits
        except Exception:
            return []

    def get_git_status(self) -> Dict[str, Any]:
        """Get current git status."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    files.append(line.strip())
            return {"files": files}
        except Exception:
            return {"files": []}

    def get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def generate_report(self, report: EngineeringReport) -> str:
        """Generate markdown report."""
        md = f"""# Phantom Engine Engineering Report

**Generated:** {datetime.now().isoformat()}
**Task:** {report.task}
**Repository:** {report.repository}
**Git Branch:** {report.git_branch}
**Mode:** {report.mode}
**Started:** {report.started_at}
**Completed:** {report.completed_at}
**Duration:** {report.duration_seconds:.1f} seconds
**Iterations:** {report.iterations_completed} / {report.max_iterations}

---

## Executive Summary

**Status:** {'✅ COMPLETE' if report.success else '❌ INCOMPLETE'}
**Completion:** {report.completion_percentage:.1f}%
**Final Phase:** {report.final_phase}

{report.architecture_summary}

---

## Repository Analysis

**Languages Detected:** {', '.join(report.languages_detected) if report.languages_detected else 'None'}
**Frameworks Detected:** {', '.join(report.frameworks_detected) if report.frameworks_detected else 'None'}
**Package Managers:** {', '.join(report.package_managers) if report.package_managers else 'None'}

### Architecture Summary
{report.architecture_summary or 'Not analyzed'}

---

## Problems Discovered

{self._format_problems(report.problems_discovered)}

---

## Security Findings

{self._format_security_findings(report.security_findings)}

---

## Fixes Implemented

### Bugs Fixed
{self._format_fixes(report.bugs_fixed)}

### Vulnerabilities Fixed
{self._format_fixes(report.vulnerabilities_fixed)}

---

## Files Changed

### Modified
{self._format_file_list(report.files_modified)}

### Created
{self._format_file_list(report.files_created)}

### Deleted
{self._format_file_list(report.files_deleted)}

---

## Dependency Changes

{self._format_dependencies(report.dependencies_changed)}

---

## Test Results

### Tests Executed
{self._format_tests(report.tests_executed)}

### Summary
- **Total Tests:** {report.test_results.get('total', 'N/A')}
- **Passed:** {report.test_results.get('passed', 'N/A')}
- **Failed:** {report.test_results.get('failed', 'N/A')}
- **Skipped:** {report.test_results.get('skipped', 'N/A')}
- **Coverage:** {report.coverage.get('total', 'N/A')}%

---

## Git Activity

### Commits
{self._format_commits(report.commits)}

### Push Status
{report.push_status or 'Not pushed'}

### Pull Request
{self._format_pr(report.pr_url, report.pr_number)}

---

## Deployment

**Target:** {report.deployment_target or 'Not configured'}
**Status:** {report.deployment_status}
**URL:** {report.deployment_url or 'N/A'}
**Health Check:** {'✅ Passed' if report.health_check_passed else '❌ Failed/Not Run'}

---

## Remaining Issues

{self._format_remaining_issues(report.remaining_issues)}

---

## Warnings & Errors

### Warnings
{self._format_list(report.warnings)}

### Errors
{self._format_list(report.errors)}

---

## Completion Status

**Final Status:** {report.completion_status}
**Completion Percentage:** {report.completion_percentage:.1f}%

"""
        return md

    def _format_problems(self, problems: List[Dict]) -> str:
        if not problems:
            return "No problems discovered."
        lines = []
        for i, p in enumerate(problems, 1):
            severity = p.get('severity', 'unknown').upper()
            desc = p.get('description', 'No description')
            file = p.get('file', 'Unknown file')
            lines.append(f"{i}. **[ {severity} ]** {desc} (`{file}`)")
        return '\n'.join(lines)

    def _format_security_findings(self, findings: List[Dict]) -> str:
        if not findings:
            return "No security findings."
        lines = []
        for i, f in enumerate(findings, 1):
            severity = f.get('severity', 'unknown').upper()
            desc = f.get('description', 'No description')
            file = f.get('file', 'Unknown file')
            cwe = f.get('cwe', '')
            cwe_str = f" (CWE-{cwe})" if cwe else ""
            lines.append(f"{i}. **[ {severity} ]** {desc}{cwe_str} (`{file}`)")
        return '\n'.join(lines)

    def _format_fixes(self, fixes: List[Dict]) -> str:
        if not fixes:
            return "No fixes implemented."
        lines = []
        for i, f in enumerate(fixes, 1):
            desc = f.get('description', 'No description')
            file = f.get('file', 'Unknown file')
            verified = '✅' if f.get('verified') else '⏳'
            lines.append(f"{i}. {verified} {desc} (`{file}`)")
        return '\n'.join(lines)

    def _format_file_list(self, files: List[str]) -> str:
        if not files:
            return "None"
        return '\n'.join(f"- `{f}`" for f in files)

    def _format_dependencies(self, deps: List[Dict]) -> str:
        if not deps:
            return "No dependency changes."
        lines = []
        for d in deps:
            name = d.get('name', 'unknown')
            action = d.get('action', 'changed')
            version = d.get('version', '')
            lines.append(f"- {action.capitalize()}: `{name}` {version}")
        return '\n'.join(lines)

    def _format_tests(self, tests: List[Dict]) -> str:
        if not tests:
            return "No tests executed."
        lines = []
        for t in tests:
            name = t.get('name', 'unknown')
            status = t.get('status', 'unknown')
            duration = t.get('duration', 0)
            lines.append(f"- {name}: {status} ({duration:.2f}s)")
        return '\n'.join(lines)

    def _format_commits(self, commits: List[Dict]) -> str:
        if not commits:
            return "No commits in this session."
        lines = []
        for c in commits:
            lines.append(f"- `{c['hash']}` {c['message']} ({c['author']}, {c['date']})")
        return '\n'.join(lines)

    def _format_pr(self, url: str, number: int) -> str:
        if not url:
            return "No pull request created."
        return f"- **PR #{number}:** {url}"

    def _format_remaining_issues(self, issues: List[Dict]) -> str:
        if not issues:
            return "No remaining issues."
        lines = []
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity', 'unknown').upper()
            desc = issue.get('description', 'No description')
            file = issue.get('file', 'Unknown file')
            lines.append(f"{i}. **[ {severity} ]** {desc} (`{file}`)")
        return '\n'.join(lines)

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "None"
        return '\n'.join(f"- {item}" for item in items)

    def save_report(self, report: EngineeringReport):
        """Save report to file."""
        md = self.generate_report(report)
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_file, 'w') as f:
            f.write(md)
        logger.info(f"Report saved to {self.report_file}")

    def generate_from_state(self) -> EngineeringReport:
        """Generate report from current state."""
        state = self.load_state()
        iteration_log = self.load_iteration_log()
        findings = self.load_findings()
        test_results = self.load_test_results()
        changelog = self.load_changelog()
        commits = self.get_git_commits()
        git_status = self.get_git_status()
        branch = self.get_current_branch()

        report = EngineeringReport(
            task=state.get("task", ""),
            repository=str(Path.cwd()),
            git_branch=branch,
            started_at=state.get("started_at", ""),
            completed_at=datetime.now().isoformat(),
            iterations_completed=state.get("iteration", 0),
            max_iterations=state.get("max_iterations", 10),
            mode=state.get("mode", "AUTO"),
            success=state.get("verification_complete", False),
            final_phase=state.get("phase", "unknown"),
            files_modified=[f for f in git_status.get("files", []) if f.startswith("M")],
            files_created=[f for f in git_status.get("files", []) if f.startswith("?")],
            test_results=test_results,
            commits=commits,
            warnings=state.get("warnings", []),
            errors=state.get("errors", []),
            deployment_status=state.get("deployment_status", "not_started"),
            completion_status="complete" if state.get("verification_complete") else "incomplete",
            completion_percentage=min(100, (state.get("iteration", 0) / state.get("max_iterations", 10)) * 100)
        )

        # Calculate duration
        if report.started_at:
            try:
                start = datetime.fromisoformat(report.started_at)
                end = datetime.fromisoformat(report.completed_at)
                report.duration_seconds = (end - start).total_seconds()
            except Exception:
                pass

        return report


if __name__ == "__main__":
    import sys

    rg = ReportGenerator()

    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <command> [args...]")
        print("Commands: generate, generate-from-state")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "generate-from-state":
        report = rg.generate_from_state()
        rg.save_report(report)
        print("Report generated and saved")
    elif cmd == "generate":
        # Create sample report
        report = EngineeringReport(
            task="Sample task",
            repository="/sample/repo",
            git_branch="main",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            mode="AUTO",
            success=True,
            architecture_summary="Sample architecture",
            languages_detected=["Python", "TypeScript"],
            frameworks_detected=["FastAPI", "React"],
            package_managers=["pip", "npm"],
            problems_discovered=[
                {"severity": "high", "description": "SQL injection vulnerability", "file": "api/users.py"},
                {"severity": "medium", "description": "Missing input validation", "file": "api/auth.py"}
            ],
            security_findings=[
                {"severity": "critical", "description": "Hardcoded API key", "file": "config.py", "cwe": "798"}
            ],
            bugs_fixed=[
                {"description": "Fixed SQL injection", "file": "api/users.py", "verified": True}
            ],
            files_modified=["api/users.py", "config.py"],
            test_results={"total": 42, "passed": 40, "failed": 2, "skipped": 0},
            coverage={"total": 85.5},
            commits=[{"hash": "abc1234", "message": "Fix SQL injection", "author": "Phantom", "date": "2024-01-01T00:00:00"}],
            push_status="Pushed to origin/feature/fix",
            pr_url="https://github.com/user/repo/pull/1",
            pr_number=1,
            deployment_status="success",
            deployment_target="vercel",
            deployment_url="https://app.vercel.com",
            health_check_passed=True,
            completion_status="complete",
            completion_percentage=100
        )
        rg.save_report(report)
        print("Sample report generated")
    else:
        print(f"Unknown command: {cmd}")