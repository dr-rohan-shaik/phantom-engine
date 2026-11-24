"""
Phantom Engine GitHub Manager
Handles GitHub operations: PR creation, CI monitoring, issue tracking.
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class PullRequest:
    """Pull request information."""
    number: int = 0
    url: str = ""
    title: str = ""
    body: str = ""
    state: str = "open"
    head_branch: str = ""
    base_branch: str = "main"
    draft: bool = False
    created_at: str = ""
    updated_at: str = ""
    merged: bool = False
    mergeable: bool = True


@dataclass
class CIStatus:
    """CI/CD status for a branch or PR."""
    status: str = "unknown"  # success, failure, pending, unknown
    workflow_name: str = ""
    run_id: str = ""
    url: str = ""
    conclusion: str = ""
    created_at: str = ""
    updated_at: str = ""


class GitHubManager:
    """Manages GitHub operations via gh CLI."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self._check_gh_auth()

    def _check_gh_auth(self) -> bool:
        """Check if gh is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_gh(self, args: List[str], capture=True, timeout=30) -> subprocess.CompletedProcess:
        """Run a gh command."""
        cmd = ["gh"] + args
        logger.debug(f"Running: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=capture,
            text=True,
            timeout=timeout
        )

    def get_repo_info(self) -> Dict[str, Any]:
        """Get repository information."""
        try:
            result = self._run_gh(["repo", "view", "--json", "name,owner,url,defaultBranchRef"])
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception as e:
            logger.error(f"Failed to get repo info: {e}")
            return {}

    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None
    ) -> Optional[PullRequest]:
        """Create a pull request."""
        try:
            cmd = [
                "pr", "create",
                "--title", title,
                "--body", body,
                "--head", head_branch,
                "--base", base_branch
            ]
            if draft:
                cmd.append("--draft")
            if labels:
                cmd.extend(["--label", ",".join(labels)])

            result = self._run_gh(cmd)

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                pr_number = int(pr_url.split('/')[-1]) if pr_url else 0

                # Get full PR details
                pr = self.get_pull_request(pr_number)
                if pr:
                    return pr

                # Fallback
                return PullRequest(
                    number=pr_number,
                    url=pr_url,
                    title=title,
                    body=body,
                    head_branch=head_branch,
                    base_branch=base_branch,
                    draft=draft,
                    created_at=datetime.now().isoformat()
                )
            else:
                logger.error(f"PR creation failed: {result.stderr}")
                return None
        except Exception as e:
            logger.exception("PR creation failed")
            return None

    def get_pull_request(self, pr_number: int) -> Optional[PullRequest]:
        """Get pull request details."""
        try:
            result = self._run_gh([
                "pr", "view", str(pr_number),
                "--json", "number,url,title,body,state,headRefName,baseRefName,isDraft,createdAt,updatedAt,merged,mergeable"
            ])
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return PullRequest(
                    number=data.get("number", 0),
                    url=data.get("url", ""),
                    title=data.get("title", ""),
                    body=data.get("body", ""),
                    state=data.get("state", "open"),
                    head_branch=data.get("headRefName", ""),
                    base_branch=data.get("baseRefName", "main"),
                    draft=data.get("isDraft", False),
                    created_at=data.get("createdAt", ""),
                    updated_at=data.get("updatedAt", ""),
                    merged=data.get("merged", False),
                    mergeable=data.get("mergeable", True)
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get PR {pr_number}: {e}")
            return None

    def list_pull_requests(self, state: str = "open", limit: int = 10) -> List[PullRequest]:
        """List pull requests."""
        try:
            result = self._run_gh([
                "pr", "list",
                "--state", state,
                "--limit", str(limit),
                "--json", "number,url,title,state,headRefName,baseRefName,isDraft,createdAt,updatedAt,merged"
            ])
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [
                    PullRequest(
                        number=item.get("number", 0),
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        state=item.get("state", "open"),
                        head_branch=item.get("headRefName", ""),
                        base_branch=item.get("baseRefName", "main"),
                        draft=item.get("isDraft", False),
                        created_at=item.get("createdAt", ""),
                        updated_at=item.get("updatedAt", ""),
                        merged=item.get("merged", False)
                    )
                    for item in data
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to list PRs: {e}")
            return []

    def check_ci_status(self, branch: Optional[str] = None, pr_number: Optional[int] = None) -> List[CIStatus]:
        """Check CI status for a branch or PR."""
        try:
            cmd = ["run", "list"]
            if pr_number:
                cmd.extend(["--pr", str(pr_number)])
            elif branch:
                cmd.extend(["--branch", branch])
            cmd.extend(["--limit", "20", "--json", "name,status,conclusion,url,createdAt,updatedAt,databaseId"])

            result = self._run_gh(cmd)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [
                    CIStatus(
                        status=item.get("status", "unknown"),
                        workflow_name=item.get("name", ""),
                        run_id=str(item.get("databaseId", "")),
                        url=item.get("url", ""),
                        conclusion=item.get("conclusion", ""),
                        created_at=item.get("createdAt", ""),
                        updated_at=item.get("updatedAt", "")
                    )
                    for item in data
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to check CI status: {e}")
            return []

    def wait_for_ci(
        self,
        branch: Optional[str] = None,
        pr_number: Optional[int] = None,
        timeout_seconds: int = 300,
        poll_interval: int = 15
    ) -> bool:
        """Wait for CI to complete successfully."""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            statuses = self.check_ci_status(branch=branch, pr_number=pr_number)

            if not statuses:
                logger.info("No CI runs found, waiting...")
                time.sleep(poll_interval)
                continue

            # Check if all runs are complete
            all_complete = all(s.status == "completed" for s in statuses)
            if not all_complete:
                logger.info("CI still running...")
                time.sleep(poll_interval)
                continue

            # Check if all successful
            all_success = all(s.conclusion == "success" for s in statuses)
            if all_success:
                logger.info("All CI checks passed!")
                return True
            else:
                failed = [s for s in statuses if s.conclusion == "failure"]
                logger.error(f"CI failed: {failed}")
                return False

        logger.warning("CI timeout reached")
        return False

    def merge_pull_request(self, pr_number: int, method: str = "merge", delete_branch: bool = True) -> bool:
        """Merge a pull request."""
        try:
            cmd = ["pr", "merge", str(pr_number), f"--{method}"]
            if delete_branch:
                cmd.append("--delete-branch")

            result = self._run_gh(cmd)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"PR merge failed: {e}")
            return False

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a GitHub issue."""
        try:
            cmd = ["issue", "create", "--title", title, "--body", body]
            if labels:
                cmd.extend(["--label", ",".join(labels)])
            if assignees:
                cmd.extend(["--assignee", ",".join(assignees)])

            result = self._run_gh(cmd)
            if result.returncode == 0:
                issue_url = result.stdout.strip()
                issue_number = int(issue_url.split('/')[-1]) if issue_url else 0
                return {"number": issue_number, "url": issue_url}
            return None
        except Exception as e:
            logger.error(f"Issue creation failed: {e}")
            return None

    def add_pr_comment(self, pr_number: int, body: str) -> bool:
        """Add a comment to a PR."""
        try:
            result = self._run_gh(["pr", "comment", str(pr_number), "--body", body])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to add PR comment: {e}")
            return False


if __name__ == "__main__":
    import sys

    gm = GitHubManager()

    if len(sys.argv) < 2:
        print("Usage: python github_manager.py <command> [args...]")
        print("Commands: repo-info, create-pr, get-pr, list-prs, ci-status, wait-ci, merge-pr, create-issue")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "repo-info":
        print(json.dumps(gm.get_repo_info(), indent=2))
    elif cmd == "create-pr":
        if len(sys.argv) > 5:
            print(json.dumps(gm.create_pull_request(
                sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
            ).__dict__ if gm.create_pull_request(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]) else None, indent=2))
        else:
            print("Usage: create-pr <title> <body> <head> <base>")
    elif cmd == "get-pr":
        if len(sys.argv) > 2:
            pr = gm.get_pull_request(int(sys.argv[2]))
            print(json.dumps(pr.__dict__ if pr else None, indent=2))
    elif cmd == "list-prs":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        print(json.dumps([pr.__dict__ for pr in gm.list_pull_requests(state)], indent=2))
    elif cmd == "ci-status":
        branch = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps([s.__dict__ for s in gm.check_ci_status(branch=branch)], indent=2))
    elif cmd == "wait-ci":
        branch = sys.argv[2] if len(sys.argv) > 2 else None
        print(gm.wait_for_ci(branch=branch))
    else:
        print(f"Unknown command: {cmd}")