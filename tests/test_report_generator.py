"""
Tests for Phantom Engine Report Generator
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from scripts.report_generator import ReportGenerator, EngineeringReport


class TestReportGenerator:
    """Test cases for ReportGenerator."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def report_gen(self, temp_dir):
        return ReportGenerator(phantom_dir=temp_dir / ".phantom")

    def test_generate_report_basic(self, report_gen):
        """Test basic report generation."""
        report = EngineeringReport(
            task="Test task",
            repository="/test/repo",
            git_branch="main",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            mode="AUTO",
            success=True,
            architecture_summary="Test architecture",
            languages_detected=["Python", "TypeScript"],
            frameworks_detected=["FastAPI", "React"],
            package_managers=["pip", "npm"]
        )

        md = report_gen.generate_report(report)

        assert "Phantom Engine Engineering Report" in md
        assert "Test task" in md
        assert "Test architecture" in md
        assert "Python" in md
        assert "TypeScript" in md
        assert "FastAPI" in md
        assert "React" in md

    def test_generate_report_with_problems(self, report_gen):
        """Test report with problems discovered."""
        report = EngineeringReport(
            task="Test",
            problems_discovered=[
                {"severity": "high", "description": "SQL injection", "file": "api.py"},
                {"severity": "medium", "description": "Missing validation", "file": "auth.py"}
            ]
        )

        md = report_gen.generate_report(report)

        assert "SQL injection" in md
        assert "HIGH" in md
        assert "MEDIUM" in md
        assert "api.py" in md

    def test_generate_report_with_fixes(self, report_gen):
        """Test report with fixes."""
        report = EngineeringReport(
            task="Test",
            bugs_fixed=[
                {"description": "Fixed SQL injection", "file": "api.py", "verified": True},
                {"description": "Added validation", "file": "auth.py", "verified": False}
            ]
        )

        md = report_gen.generate_report(report)

        assert "Fixed SQL injection" in md
        assert "✅" in md  # verified
        assert "⏳" in md  # not verified

    def test_generate_report_with_security(self, report_gen):
        """Test report with security findings."""
        report = EngineeringReport(
            task="Test",
            security_findings=[
                {"severity": "critical", "description": "Hardcoded secret", "file": "config.py", "cwe": "798"}
            ]
        )

        md = report_gen.generate_report(report)

        assert "CRITICAL" in md
        assert "Hardcoded secret" in md
        assert "CWE-798" in md

    def test_generate_report_with_files(self, report_gen):
        """Test report with file changes."""
        report = EngineeringReport(
            task="Test",
            files_modified=["file1.py", "file2.py"],
            files_created=["file3.py"],
            files_deleted=["old.py"]
        )

        md = report_gen.generate_report(report)

        assert "file1.py" in md
        assert "file2.py" in md
        assert "file3.py" in md
        assert "old.py" in md

    def test_generate_report_with_commits(self, report_gen):
        """Test report with git commits."""
        report = EngineeringReport(
            task="Test",
            commits=[
                {"hash": "abc1234", "message": "Fix bug", "author": "Phantom", "date": "2024-01-01T00:00:00"},
                {"hash": "def5678", "message": "Add test", "author": "Phantom", "date": "2024-01-01T01:00:00"}
            ]
        )

        md = report_gen.generate_report(report)

        assert "abc1234" in md
        assert "Fix bug" in md
        assert "def5678" in md

    def test_generate_report_with_pr(self, report_gen):
        """Test report with PR info."""
        report = EngineeringReport(
            task="Test",
            pr_url="https://github.com/user/repo/pull/1",
            pr_number=1
        )

        md = report_gen.generate_report(report)

        assert "PR #1" in md
        assert "https://github.com/user/repo/pull/1" in md

    def test_generate_report_with_deployment(self, report_gen):
        """Test report with deployment info."""
        report = EngineeringReport(
            task="Test",
            deployment_status="success",
            deployment_target="vercel",
            deployment_url="https://app.vercel.app",
            health_check_passed=True
        )

        md = report_gen.generate_report(report)

        assert "vercel" in md
        assert "https://app.vercel.app" in md
        assert "✅ Passed" in md

    def test_save_report(self, report_gen, temp_dir):
        """Test saving report to file."""
        report = EngineeringReport(task="Test")
        report_gen.save_report(report)

        report_file = temp_dir / ".phantom" / "final-report.md"
        assert report_file.exists()

        content = report_file.read_text()
        assert "Phantom Engine Engineering Report" in content

    @patch("scripts.report_generator.subprocess.run")
    def test_get_git_commits(self, mock_run, report_gen):
        """Test getting git commits."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc1234|Phantom|2024-01-01T00:00:00|Fix bug\ndef5678|Phantom|2024-01-01T01:00:00|Add test"
        )

        commits = report_gen.get_git_commits()

        assert len(commits) == 2
        assert commits[0]["hash"] == "abc1234"
        assert commits[0]["message"] == "Fix bug"

    @patch("scripts.report_generator.subprocess.run")
    def test_get_git_status(self, mock_run, report_gen):
        """Test getting git status."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="M file1.py\n?? file2.py"
        )

        status = report_gen.get_git_status()

        assert "M file1.py" in status["files"]
        assert "?? file2.py" in status["files"]

    @patch("scripts.report_generator.subprocess.run")
    def test_get_current_branch(self, mock_run, report_gen):
        """Test getting current branch."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feature/test\n"
        )

        branch = report_gen.get_current_branch()
        assert branch == "feature/test"

    def test_generate_from_state(self, report_gen, temp_dir):
        """Test generating report from state files."""
        phantom_dir = temp_dir / ".phantom"
        phantom_dir.mkdir()

        # Create state file
        state = {
            "active": True,
            "mode": "AUTO",
            "iteration": 3,
            "max_iterations": 10,
            "task": "Test task",
            "phase": "testing",
            "verification_complete": True,
            "started_at": "2024-01-01T00:00:00",
            "warnings": ["Test warning"],
            "errors": ["Test error"],
            "deployment_status": "success"
        }
        (phantom_dir / "state.json").write_text(json.dumps(state))

        # Create test results
        (phantom_dir / "test-results.json").write_text(json.dumps({
            "total": 100,
            "passed": 95,
            "failed": 5
        }))

        report = report_gen.generate_from_state()

        assert report.task == "Test task"
        assert report.iterations_completed == 3
        assert report.success is True
        assert "Test warning" in report.warnings
        assert "Test error" in report.errors


class TestEngineeringReport:
    """Test EngineeringReport dataclass."""

    def test_defaults(self):
        """Test default values."""
        report = EngineeringReport()

        assert report.task == ""
        assert report.mode == "AUTO"
        assert report.success is False
        assert report.languages_detected == []
        assert report.frameworks_detected == []
        assert report.problems_discovered == []
        assert report.completion_status == "incomplete"

    def test_all_fields(self):
        """Test setting all fields."""
        report = EngineeringReport(
            task="Full test",
            repository="/repo",
            git_branch="main",
            success=True,
            languages_detected=["Python"],
            problems_discovered=[{"desc": "test"}],
            files_modified=["file.py"]
        )

        assert report.task == "Full test"
        assert report.languages_detected == ["Python"]
        assert len(report.problems_discovered) == 1
        assert report.files_modified == ["file.py"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])