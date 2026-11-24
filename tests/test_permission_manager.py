"""
Tests for Phantom Engine Permission Manager
"""

import json
import tempfile
import pytest
from pathlib import Path

from scripts.permission_manager import PermissionManager, PermissionPolicy, PermissionMode


class TestPermissionManager:
    """Test cases for PermissionManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def perm_manager(self, temp_dir):
        """Create PermissionManager with temp directory."""
        return PermissionManager(config_path=temp_dir / ".phantom" / "permissions.json")

    def test_default_policy(self, perm_manager):
        """Test default permission policy."""
        policy = perm_manager.policy
        assert policy.mode == PermissionMode.AUTO
        assert "rm -rf /" in policy.blocked_commands
        assert "git push --force" in policy.require_approval
        assert "git add" in policy.auto_approve_patterns

    def test_set_mode(self, perm_manager):
        """Test setting permission mode."""
        perm_manager.set_mode(PermissionMode.SAFE)
        assert perm_manager.get_mode() == PermissionMode.SAFE

        perm_manager.set_mode(PermissionMode.SANDBOX)
        assert perm_manager.get_mode() == PermissionMode.SANDBOX

    def test_check_command_safe_mode(self, perm_manager):
        """Test command checking in SAFE mode."""
        perm_manager.set_mode(PermissionMode.SAFE)

        # Should require approval for unlisted command
        result = perm_manager.check_command("echo hello")
        assert result["allowed"] is True
        assert result["requires_approval"] is True
        assert "SAFE mode" in result["reason"]

    def test_check_command_auto_mode(self, perm_manager):
        """Test command checking in AUTO mode."""
        perm_manager.set_mode(PermissionMode.AUTO)

        # Should auto-approve unlisted command
        result = perm_manager.check_command("echo hello")
        assert result["allowed"] is True
        assert result["requires_approval"] is False
        assert "AUTO mode" in result["reason"]

    def test_check_command_auto_approve_patterns(self, perm_manager):
        """Test auto-approve patterns."""
        perm_manager.set_mode(PermissionMode.SAFE)  # Even in SAFE mode

        # git add should be auto-approved
        result = perm_manager.check_command("git add .")
        assert result["allowed"] is True
        assert result["requires_approval"] is False
        assert "Auto-approved" in result["reason"]

        # npm install should be auto-approved
        result = perm_manager.check_command("npm install")
        assert result["allowed"] is True
        assert result["requires_approval"] is False

    def test_check_command_blocked(self, perm_manager):
        """Test blocked commands."""
        result = perm_manager.check_command("rm -rf /")
        assert result["allowed"] is False
        assert result["requires_approval"] is False
        assert "blocked pattern" in result["reason"]

    def test_check_command_requires_approval(self, perm_manager):
        """Test commands requiring explicit approval."""
        perm_manager.set_mode(PermissionMode.AUTO)

        result = perm_manager.check_command("git push --force origin main")
        assert result["allowed"] is True
        assert result["requires_approval"] is True
        assert "Requires explicit approval" in result["reason"]

    def test_check_dangerous_action(self, perm_manager):
        """Test dangerous action checking."""
        # SAFE mode blocks dangerous actions
        perm_manager.set_mode(PermissionMode.SAFE)
        result = perm_manager.check_dangerous_action("force_push")
        assert result["allowed"] is False
        assert result["requires_approval"] is True

        # AUTO mode allows but requires approval
        perm_manager.set_mode(PermissionMode.AUTO)
        result = perm_manager.check_dangerous_action("force_push")
        assert result["allowed"] is True
        assert result["requires_approval"] is True

        # SANDBOX mode allows without approval
        perm_manager.set_mode(PermissionMode.SANDBOX)
        result = perm_manager.check_dangerous_action("force_push")
        assert result["allowed"] is True
        assert result["requires_approval"] is False

    def test_audit_log(self, perm_manager):
        """Test audit logging."""
        perm_manager.check_command("echo test")
        perm_manager.check_command("git add file.txt")

        log = perm_manager.get_audit_log()
        assert len(log) == 2
        assert log[0]["command"] == "echo test"
        assert log[1]["command"] == "git add file.txt"

    def test_save_and_load_policy(self, perm_manager, temp_dir):
        """Test policy persistence."""
        perm_manager.set_mode(PermissionMode.SAFE)
        perm_manager.policy.allowed_commands.add("custom-command")
        perm_manager.save_policy()

        # Create new manager and load
        new_manager = PermissionManager(config_path=temp_dir / ".phantom" / "permissions.json")
        assert new_manager.get_mode() == PermissionMode.SAFE
        assert "custom-command" in new_manager.policy.allowed_commands

    def test_sandbox_config(self, perm_manager):
        """Test sandbox configuration generation."""
        config = perm_manager.create_sandbox_config()

        assert config["mode"] == "SANDBOX"
        assert "requirements" in config
        assert "launch_command" in config
        assert "environment_variables" in config
        assert "warning" in config


class TestPermissionPolicy:
    """Test PermissionPolicy dataclass."""

    def test_defaults(self):
        """Test default values."""
        policy = PermissionPolicy()

        assert policy.mode == PermissionMode.AUTO
        assert isinstance(policy.allowed_commands, set)
        assert isinstance(policy.blocked_commands, set)
        assert isinstance(policy.require_approval, set)
        assert isinstance(policy.auto_approve_patterns, list)
        assert isinstance(policy.dangerous_actions, set)

    def test_custom_values(self):
        """Test custom policy values."""
        policy = PermissionPolicy(
            mode=PermissionMode.SAFE,
            allowed_commands={"custom-cmd"},
            blocked_commands={"bad-cmd"},
            require_approval={"careful-cmd"},
            auto_approve_patterns=["safe-"],
            dangerous_actions={"very-dangerous"}
        )

        assert policy.mode == PermissionMode.SAFE
        assert "custom-cmd" in policy.allowed_commands
        assert "bad-cmd" in policy.blocked_commands
        assert "careful-cmd" in policy.require_approval
        assert "safe-" in policy.auto_approve_patterns
        assert "very-dangerous" in policy.dangerous_actions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])