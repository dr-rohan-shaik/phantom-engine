"""
Tests for Phantom Engine Git Manager
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from scripts.git_manager import GitManager, GitStatus, CommitResult


class TestGitManager:
    """Test cases for GitManager."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock git repository."""
        with patch("scripts.git_manager.subprocess.run") as mock_run:
            # Mock git rev-parse --git-dir
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            yield mock_run

    @pytest.fixture
    def git_manager(self, mock_repo):
        """Create GitManager with mocked repo."""
        return GitManager(repo_path=Path("/fake/repo"))

    def test_get_status(self, git_manager, mock_repo):
        """Test getting git status."""
        # Setup mock responses
        mock_repo.side_effect = [
            MagicMock(returncode=0, stdout="true"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout="main"),  # branch --show-current
            MagicMock(returncode=0, stdout="https://github.com/user/repo.git"),  # remote url
            MagicMock(returncode=0, stdout="file1.py\nfile2.py"),  # staged
            MagicMock(returncode=0, stdout="file3.py"),  # unstaged
            MagicMock(returncode=0, stdout="file4.py"),  # untracked
            MagicMock(returncode=0, stdout="2\t1"),  # ahead/behind
        ]

        status = git_manager.get_status()

        assert status.is_repo is True
        assert status.current_branch == "main"
        assert status.remote_url == "https://github.com/user/repo.git"
        assert status.staged_files == ["file1.py", "file2.py"]
        assert status.unstaged_files == ["file3.py"]
        assert status.untracked_files == ["file4.py"]
        assert status.has_changes is True
        assert status.ahead == 2
        assert status.behind == 1

    def test_get_status_not_repo(self, git_manager, mock_repo):
        """Test status when not in a git repo."""
        mock_repo.return_value = MagicMock(returncode=1, stdout="")

        status = git_manager.get_status()

        assert status.is_repo is False

    def test_create_branch(self, git_manager, mock_repo):
        """Test branch creation."""
        mock_repo.return_value = MagicMock(returncode=0)

        result = git_manager.create_branch("feature/test", "main")

        assert result is True
        calls = mock_repo.call_args_list
        assert any("checkout" in str(c) and "main" in str(c) for c in calls)
        assert any("checkout" in str(c) and "-b" in str(c) and "feature/test" in str(c) for c in calls)

    def test_commit_success(self, git_manager, mock_repo):
        """Test successful commit."""
        # Mock status with staged files
        with patch.object(git_manager, "get_status") as mock_status:
            mock_status.return_value = GitStatus(
                is_repo=True,
                current_branch="main",
                has_changes=True,
                staged_files=["file1.py", "file2.py"]
            )

            mock_repo.side_effect = [
                MagicMock(returncode=0),  # commit
                MagicMock(returncode=0, stdout="abc12345\n")  # rev-parse
            ]

            result = git_manager.commit("Test commit message")

            assert result.success is True
            assert result.commit_hash == "abc12345"
            assert result.message == "Test commit message"
            assert result.files_committed == ["file1.py", "file2.py"]

    def test_commit_nothing_staged(self, git_manager, mock_repo):
        """Test commit with nothing staged."""
        with patch.object(git_manager, "get_status") as mock_status:
            mock_status.return_value = GitStatus(
                is_repo=True,
                current_branch="main",
                has_changes=False,
                staged_files=[]
            )

            result = git_manager.commit("Test commit")

            assert result.success is False
            assert "No staged changes" in result.error

    def test_commit_failure(self, git_manager, mock_repo):
        """Test commit failure."""
        with patch.object(git_manager, "get_status") as mock_status:
            mock_status.return_value = GitStatus(
                is_repo=True,
                current_branch="main",
                has_changes=True,
                staged_files=["file1.py"]
            )

            mock_repo.return_value = MagicMock(returncode=1, stderr="Commit failed")

            result = git_manager.commit("Test commit")

            assert result.success is False
            assert "Commit failed" in result.error

    def test_push(self, git_manager, mock_repo):
        """Test push."""
        mock_repo.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_manager.push()

        assert result is True

    def test_push_force(self, git_manager, mock_repo):
        """Test force push."""
        mock_repo.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_manager.push(force=True)

        assert result is True
        args = mock_repo.call_args[0][0]
        assert "--force-with-lease" in args

    def test_create_checkpoint(self, git_manager, mock_repo):
        """Test checkpoint creation."""
        mock_repo.return_value = MagicMock(returncode=0)

        tag = git_manager.create_checkpoint("test")

        assert tag.startswith("test-")
        assert len(tag) > 10  # includes timestamp

    def test_get_diff(self, git_manager, mock_repo):
        """Test getting diff."""
        mock_repo.return_value = MagicMock(returncode=0, stdout="diff content")

        diff = git_manager.get_diff()

        assert diff == "diff content"

    def test_get_log(self, git_manager, mock_repo):
        """Test getting commit log."""
        mock_repo.return_value = MagicMock(
            returncode=0,
            stdout="abc1234 Fix bug\ndef5678 Add feature"
        )

        log = git_manager.get_log(limit=2, oneline=True)

        assert len(log) == 2
        assert log[0]["hash"] == "abc1234"
        assert log[0]["message"] == "Fix bug"

    def test_preserve_user_changes(self, git_manager, mock_repo):
        """Test preserving user changes."""
        with patch.object(git_manager, "get_status") as mock_status:
            mock_status.return_value = GitStatus(
                is_repo=True,
                has_changes=True
            )
            mock_repo.return_value = MagicMock(returncode=0)

            result = git_manager.preserve_user_changes()

            assert result is True
            args = mock_repo.call_args[0][0]
            assert "stash" in args
            assert "push" in args

    def test_restore_user_changes(self, git_manager, mock_repo):
        """Test restoring user changes."""
        mock_repo.return_value = MagicMock(returncode=0)

        result = git_manager.restore_user_changes()

        assert result is True
        args = mock_repo.call_args[0][0]
        assert "stash" in args
        assert "pop" in args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])