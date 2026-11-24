"""
Phantom Engine Git Manager
Handles Git operations: status, branching, commits, pushing, and GitHub integration.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git repository status."""
    is_repo: bool = False
    current_branch: str = ""
    has_changes: bool = False
    staged_files: List[str] = None
    unstaged_files: List[str] = None
    untracked_files: List[str] = None
    ahead: int = 0
    behind: int = 0
    remote_url: str = ""

    def __post_init__(self):
        if self.staged_files is None:
            self.staged_files = []
        if self.unstaged_files is None:
            self.unstaged_files = []
        if self.untracked_files is None:
            self.untracked_files = []


@dataclass
class CommitResult:
    """Result of a commit operation."""
    success: bool
    commit_hash: str = ""
    message: str = ""
    files_committed: List[str] = None
    error: str = ""

    def __post_init__(self):
        if self.files_committed is None:
            self.files_committed = []


class GitManager:
    """Manages Git operations for Phantom Engine."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self._validate_repo()

    def _validate_repo(self):
        """Validate that we're in a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise ValueError(f"Not a git repository: {self.repo_path}")
        except Exception as e:
            raise ValueError(f"Git validation failed: {e}")

    def _run_git(self, args: List[str], capture=True, timeout=30) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git"] + args
        logger.debug(f"Running: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=capture,
            text=True,
            timeout=timeout
        )

    def get_status(self) -> GitStatus:
        """Get comprehensive git status."""
        status = GitStatus()

        # Check if repo
        result = self._run_git(["rev-parse", "--is-inside-work-tree"])
        status.is_repo = result.returncode == 0

        if not status.is_repo:
            return status

        # Current branch
        result = self._run_git(["branch", "--show-current"])
        status.current_branch = result.stdout.strip() or "detached"

        # Remote URL
        result = self._run_git(["config", "--get", "remote.origin.url"])
        status.remote_url = result.stdout.strip()

        # Staged files
        result = self._run_git(["diff", "--cached", "--name-only"])
        status.staged_files = [f for f in result.stdout.strip().split('\n') if f]

        # Unstaged files
        result = self._run_git(["diff", "--name-only"])
        status.unstaged_files = [f for f in result.stdout.strip().split('\n') if f]

        # Untracked files
        result = self._run_git(["ls-files", "--others", "--exclude-standard"])
        status.untracked_files = [f for f in result.stdout.strip().split('\n') if f]

        status.has_changes = bool(status.staged_files or status.unstaged_files or status.untracked_files)

        # Ahead/behind
        try:
            result = self._run_git(["rev-list", "--left-right", "--count", f"{status.current_branch}...origin/{status.current_branch}"])
            if result.returncode == 0:
                parts = result.stdout.strip().split('\t')
                if len(parts) == 2:
                    status.ahead = int(parts[0])
                    status.behind = int(parts[1])
        except Exception:
            pass

        return status

    def create_branch(self, branch_name: str, base: Optional[str] = None) -> bool:
        """Create and checkout a new branch."""
        try:
            if base:
                self._run_git(["checkout", base])
            self._run_git(["checkout", "-b", branch_name])
            logger.info(f"Created and checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def checkout_branch(self, branch_name: str, create: bool = False) -> bool:
        """Checkout an existing branch or create new."""
        try:
            if create:
                self._run_git(["checkout", "-b", branch_name])
            else:
                self._run_git(["checkout", branch_name])
            return True
        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False

    def add_files(self, files: Optional[List[str]] = None) -> bool:
        """Stage files for commit."""
        try:
            if files:
                self._run_git(["add"] + files)
            else:
                self._run_git(["add", "-A"])
            return True
        except Exception as e:
            logger.error(f"Failed to stage files: {e}")
            return False

    def commit(self, message: str, author: Optional[str] = None) -> CommitResult:
        """Create a commit with the given message."""
        try:
            # Check if there's anything to commit
            status = self.get_status()
            if not status.staged_files:
                return CommitResult(
                    success=False,
                    error="No staged changes to commit"
                )

            # Build commit command
            cmd = ["commit", "-m", message]
            if author:
                cmd.extend(["--author", author])

            result = self._run_git(cmd)

            if result.returncode == 0:
                # Get commit hash
                hash_result = self._run_git(["rev-parse", "HEAD"])
                commit_hash = hash_result.stdout.strip()[:8]

                return CommitResult(
                    success=True,
                    commit_hash=commit_hash,
                    message=message,
                    files_committed=status.staged_files.copy()
                )
            else:
                return CommitResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            logger.exception("Commit failed")
            return CommitResult(success=False, error=str(e))

    def push(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> bool:
        """Push commits to remote."""
        try:
            if branch is None:
                status = self.get_status()
                branch = status.current_branch

            cmd = ["push"]
            if force:
                cmd.append("--force-with-lease")
            cmd.extend([remote, branch])

            result = self._run_git(cmd, timeout=60)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Push failed: {e}")
            return False

    def create_checkpoint(self, label: str = "phantom-checkpoint") -> str:
        """Create a git checkpoint (lightweight tag)."""
        tag_name = f"{label}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            self._run_git(["tag", tag_name])
            logger.info(f"Created checkpoint: {tag_name}")
            return tag_name
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return ""

    def stash_changes(self, message: Optional[str] = None) -> bool:
        """Stash uncommitted changes."""
        try:
            cmd = ["stash", "push"]
            if message:
                cmd.extend(["-m", message])
            else:
                cmd.extend(["-m", f"phantom-stash-{datetime.now().isoformat()}"])

            result = self._run_git(cmd)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Stash failed: {e}")
            return False

    def pop_stash(self) -> bool:
        """Pop the latest stash."""
        try:
            result = self._run_git(["stash", "pop"])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Stash pop failed: {e}")
            return False

    def get_diff(self, staged: bool = False) -> str:
        """Get diff of changes."""
        try:
            cmd = ["diff"]
            if staged:
                cmd.append("--cached")
            result = self._run_git(cmd)
            return result.stdout
        except Exception as e:
            logger.error(f"Diff failed: {e}")
            return ""

    def get_log(self, limit: int = 10, oneline: bool = True) -> List[Dict[str, Any]]:
        """Get recent commit log."""
        try:
            cmd = ["log", f"-{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
            if oneline:
                cmd = ["log", f"-{limit}", "--oneline"]

            result = self._run_git(cmd)
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                if oneline:
                    parts = line.split(' ', 1)
                    commits.append({"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""})
                else:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            return commits
        except Exception as e:
            logger.error(f"Log failed: {e}")
            return []

    def preserve_user_changes(self) -> bool:
        """Preserve unrelated user changes by stashing."""
        status = self.get_status()
        if status.has_changes:
            return self.stash_changes("phantom-preserved-user-changes")
        return True

    def restore_user_changes(self) -> bool:
        """Restore previously stashed user changes."""
        return self.pop_stash()


if __name__ == "__main__":
    import sys
    import json

    gm = GitManager()

    if len(sys.argv) < 2:
        print("Usage: python git_manager.py <command> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        status = gm.get_status()
        print(json.dumps({
            "is_repo": status.is_repo,
            "current_branch": status.current_branch,
            "has_changes": status.has_changes,
            "staged_files": status.staged_files,
            "unstaged_files": status.unstaged_files,
            "untracked_files": status.untracked_files,
            "ahead": status.ahead,
            "behind": status.behind,
            "remote_url": status.remote_url
        }, indent=2))
    elif cmd == "branch":
        if len(sys.argv) > 2:
            branch = sys.argv[2]
            base = sys.argv[3] if len(sys.argv) > 3 else None
            print(gm.create_branch(branch, base))
        else:
            print("Branch name required")
    elif cmd == "commit":
        if len(sys.argv) > 2:
            msg = " ".join(sys.argv[2:])
            result = gm.commit(msg)
            print(json.dumps({
                "success": result.success,
                "commit_hash": result.commit_hash,
                "message": result.message,
                "files_committed": result.files_committed,
                "error": result.error
            }, indent=2))
        else:
            print("Commit message required")
    elif cmd == "push":
        force = "--force" in sys.argv
        print(gm.push(force=force))
    elif cmd == "checkpoint":
        label = sys.argv[2] if len(sys.argv) > 2 else "phantom-checkpoint"
        print(gm.create_checkpoint(label))
    elif cmd == "diff":
        staged = "--staged" in sys.argv
        print(gm.get_diff(staged))
    elif cmd == "log":
        print(json.dumps(gm.get_log(), indent=2))
    else:
        print(f"Unknown command: {cmd}")