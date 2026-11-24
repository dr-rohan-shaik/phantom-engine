"""
Tests for Phantom Engine GitHub Manager
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from scripts.github_manager import GitHubManager, PullRequest, CIStatus


class TestGitHubManager:
    """Test cases for GitHubManager."""

    @pytest.fixture
    def mock_gh(self):
        """Mock gh CLI."""
        with patch("scripts.github_manager.subprocess.run") as mock_run:
            yield mock_run

    @pytest.fixture
    def gh_manager(self, mock_gh):
        """Create GitHubManager with mocked gh."""
        # Mock auth check
        mock_gh.return_value = MagicMock(returncode=0)
        return GitHubManager(repo_path=Path("/fake/repo"))

    def test_get_repo_info(self, gh_manager, mock_gh):
        """Test getting repository info."""
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "name": "test-repo",
                "owner": {"login": "testuser"},
                "url": "https://github.com/testuser/test-repo",
                "defaultBranchRef": {"name": "main"}
            })
        )

        info = gh_manager.get_repo_info()

        assert info["name"] == "test-repo"
        assert info["owner"]["login"] == "testuser"

    def test_create_pull_request(self, gh_manager, mock_gh):
        """Test creating a pull request."""
        # Mock PR creation
        mock_gh.side_effect = [
            MagicMock(returncode=0, stdout="https://github.com/user/repo/pull/1\n"),  # pr create
            MagicMock(returncode=0, stdout=json.dumps({  # pr view
                "number": 1,
                "url": "https://github.com/user/repo/pull/1",
                "title": "Test PR",
                "body": "Test body",
                "state": "OPEN",
                "headRefName": "feature/test",
                "baseRefName": "main",
                "isDraft": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "merged": False,
                "mergeable": True
            }))
        ]

        pr = gh_manager.create_pull_request(
            title="Test PR",
            body="Test body",
            head_branch="feature/test",
            base_branch="main"
        )

        assert pr is not None
        assert pr.number == 1
        assert pr.title == "Test PR"
        assert pr.head_branch == "feature/test"

    def test_create_pull_request_failure(self, gh_manager, mock_gh):
        """Test PR creation failure."""
        mock_gh.return_value = MagicMock(returncode=1, stderr="PR creation failed")

        pr = gh_manager.create_pull_request("Test", "Body", "feature", "main")

        assert pr is None

    def test_get_pull_request(self, gh_manager, mock_gh):
        """Test getting PR details."""
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "number": 5,
                "url": "https://github.com/user/repo/pull/5",
                "title": "Existing PR",
                "body": "Body",
                "state": "OPEN",
                "headRefName": "feature/existing",
                "baseRefName": "main",
                "isDraft": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-02T00:00:00Z",
                "merged": False,
                "mergeable": True
            })
        )

        pr = gh_manager.get_pull_request(5)

        assert pr is not None
        assert pr.number == 5
        assert pr.title == "Existing PR"

    def test_list_pull_requests(self, gh_manager, mock_gh):
        """Test listing PRs."""
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {
                    "number": 1,
                    "url": "https://github.com/user/repo/pull/1",
                    "title": "PR 1",
                    "state": "OPEN",
                    "headRefName": "feature/1",
                    "baseRefName": "main",
                    "isDraft": False,
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                    "merged": False
                },
                {
                    "number": 2,
                    "url": "https://github.com/user/repo/pull/2",
                    "title": "PR 2",
                    "state": "MERGED",
                    "headRefName": "feature/2",
                    "baseRefName": "main",
                    "isDraft": False,
                    "createdAt": "2024-01-02T00:00:00Z",
                    "updatedAt": "2024-01-03T00:00:00Z",
                    "merged": True
                }
            ])
        )

        prs = gh_manager.list_pull_requests(state="open", limit=10)

        assert len(prs) == 2
        assert prs[0].number == 1
        assert prs[1].number == 2
        assert prs[1].merged is True

    def test_check_ci_status(self, gh_manager, mock_gh):
        """Test checking CI status."""
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {
                    "name": "Test Suite",
                    "status": "completed",
                    "conclusion": "success",
                    "url": "https://github.com/user/repo/actions/runs/1",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:05:00Z",
                    "databaseId": 123
                },
                {
                    "name": "Lint",
                    "status": "completed",
                    "conclusion": "failure",
                    "url": "https://github.com/user/repo/actions/runs/2",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:03:00Z",
                    "databaseId": 124
                }
            ])
        )

        statuses = gh_manager.check_ci_status(branch="main")

        assert len(statuses) == 2
        assert statuses[0].workflow_name == "Test Suite"
        assert statuses[0].conclusion == "success"
        assert statuses[1].workflow_name == "Lint"
        assert statuses[1].conclusion == "failure"

    @patch("scripts.github_manager.time.time")
    @patch("scripts.github_manager.time.sleep")
    def test_wait_for_ci_success(self, mock_sleep, mock_time, gh_manager, mock_gh):
        """Test waiting for CI success."""
        # Simulate time progression
        mock_time.side_effect = [0, 10, 20, 30]

        mock_gh.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps([{
                "name": "Tests",
                "status": "in_progress",
                "conclusion": "",
                "url": "",
                "createdAt": "",
                "updatedAt": "",
                "databaseId": 1
            }])),
            MagicMock(returncode=0, stdout=json.dumps([{
                "name": "Tests",
                "status": "completed",
                "conclusion": "success",
                "url": "",
                "createdAt": "",
                "updatedAt": "",
                "databaseId": 1
            }]))
        ]

        result = gh_manager.wait_for_ci(branch="main", timeout_seconds=60, poll_interval=5)

        assert result is True

    @patch("scripts.github_manager.time.time")
    @patch("scripts.github_manager.time.sleep")
    def test_wait_for_ci_failure(self, mock_sleep, mock_time, gh_manager, mock_gh):
        """Test waiting for CI failure."""
        mock_time.side_effect = [0, 10, 20, 30, 40]

        mock_gh.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps([{
                "name": "Tests",
                "status": "in_progress",
                "conclusion": "",
                "url": "",
                "createdAt": "",
                "updatedAt": "",
                "databaseId": 1
            }])),
            MagicMock(returncode=0, stdout=json.dumps([{
                "name": "Tests",
                "status": "completed",
                "conclusion": "failure",
                "url": "",
                "createdAt": "",
                "updatedAt": "",
                "databaseId": 1
            }])),
            MagicMock(returncode=0, stdout=json.dumps([{
                "name": "Tests",
                "status": "completed",
                "conclusion": "failure",
                "url": "",
                "createdAt": "",
                "updatedAt": "",
                "databaseId": 1
            }])),
        ]

        result = gh_manager.wait_for_ci(branch="main", timeout_seconds=60, poll_interval=5)

        assert result is False

    def test_merge_pull_request(self, gh_manager, mock_gh):
        """Test merging a PR."""
        mock_gh.return_value = MagicMock(returncode=0)

        result = gh_manager.merge_pull_request(1, method="squash", delete_branch=True)

        assert result is True
        args = mock_gh.call_args[0][0]
        assert "pr" in args
        assert "merge" in args
        assert "1" in args
        assert "--squash" in args
        assert "--delete-branch" in args

    def test_create_issue(self, gh_manager, mock_gh):
        """Test creating an issue."""
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo/issues/1\n"
        )

        issue = gh_manager.create_issue("Test Issue", "Issue body", labels=["bug"], assignees=["user"])

        assert issue is not None
        assert issue["number"] == 1
        assert issue["url"] == "https://github.com/user/repo/issues/1"

    def test_add_pr_comment(self, gh_manager, mock_gh):
        """Test adding a PR comment."""
        mock_gh.return_value = MagicMock(returncode=0)

        result = gh_manager.add_pr_comment(1, "Test comment")

        assert result is True
        args = mock_gh.call_args[0][0]
        assert "pr" in args
        assert "comment" in args
        assert "1" in args


class TestPullRequest:
    """Test PullRequest dataclass."""

    def test_creation(self):
        """Test PR creation."""
        pr = PullRequest(
            number=1,
            url="https://github.com/user/repo/pull/1",
            title="Test",
            body="Body",
            head_branch="feature",
            base_branch="main"
        )

        assert pr.number == 1
        assert pr.title == "Test"
        assert pr.state == "open"
        assert pr.draft is False


class TestCIStatus:
    """Test CIStatus dataclass."""

    def test_creation(self):
        """Test CI status creation."""
        ci = CIStatus(
            status="completed",
            workflow_name="Tests",
            conclusion="success"
        )

        assert ci.status == "completed"
        assert ci.workflow_name == "Tests"
        assert ci.conclusion == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])