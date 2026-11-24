"""
Phantom Engine Permission Manager
Manages the three execution modes: SAFE, AUTO, SANDBOX
"""

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json


class PermissionMode(Enum):
    """Execution permission modes."""
    SAFE = "SAFE"
    AUTO = "AUTO"
    SANDBOX = "SANDBOX"


@dataclass
class PermissionPolicy:
    """Permission policy configuration."""
    mode: PermissionMode = PermissionMode.AUTO
    allowed_commands: Set[str] = None
    blocked_commands: Set[str] = None
    require_approval: Set[str] = None
    auto_approve_patterns: List[str] = None
    dangerous_actions: Set[str] = None

    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = set()
        if self.blocked_commands is None:
            self.blocked_commands = {"rm -rf /", "dd if=/dev/zero", "format c:", "shutdown"}
        if self.require_approval is None:
            self.require_approval = {"git push --force", "docker push", "kubectl delete", "terraform destroy"}
        if self.auto_approve_patterns is None:
            self.auto_approve_patterns = [
                "git add",
                "git commit",
                "git checkout",
                "git branch",
                "npm install",
                "pip install",
                "pytest",
                "python -m pytest",
                "black",
                "ruff",
                "mypy"
            ]
        if self.dangerous_actions is None:
            self.dangerous_actions = {
                "force_push",
                "delete_branch",
                "drop_database",
                "remove_files",
                "modify_env",
                "install_global",
                "run_sudo"
            }


class PermissionManager:
    """
    Manages permissions for Phantom Engine operations.
    Implements SAFE, AUTO, and SANDBOX modes.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / ".phantom" / "permissions.json"
        self.policy = self._load_policy()
        self._audit_log: List[Dict] = []

    def _load_policy(self) -> PermissionPolicy:
        """Load permission policy from config."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                mode = PermissionMode(data.get("mode", "AUTO"))
                return PermissionPolicy(
                    mode=mode,
                    allowed_commands=set(data.get("allowed_commands", [])),
                    blocked_commands=set(data.get("blocked_commands", [])),
                    require_approval=set(data.get("require_approval", [])),
                    auto_approve_patterns=data.get("auto_approve_patterns", []),
                    dangerous_actions=set(data.get("dangerous_actions", []))
                )
            except Exception:
                pass
        return PermissionPolicy()

    def save_policy(self):
        """Save current policy to config."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "mode": self.policy.mode.value,
            "allowed_commands": list(self.policy.allowed_commands),
            "blocked_commands": list(self.policy.blocked_commands),
            "require_approval": list(self.policy.require_approval),
            "auto_approve_patterns": self.policy.auto_approve_patterns,
            "dangerous_actions": list(self.policy.dangerous_actions)
        }
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def set_mode(self, mode: PermissionMode):
        """Set permission mode."""
        self.policy.mode = mode
        self.save_policy()

    def get_mode(self) -> PermissionMode:
        """Get current permission mode."""
        return self.policy.mode

    def check_command(self, command: str) -> Dict[str, Any]:
        """
        Check if a command is allowed under current policy.
        Returns decision: {"allowed": bool, "requires_approval": bool, "reason": str}
        """
        # Check blocked commands first
        for blocked in self.policy.blocked_commands:
            if blocked in command:
                self._audit("BLOCKED", command, "Matches blocked pattern")
                return {
                    "allowed": False,
                    "requires_approval": False,
                    "reason": f"Command matches blocked pattern: {blocked}"
                }

        # Check if explicitly allowed
        for allowed in self.policy.allowed_commands:
            if allowed in command:
                self._audit("ALLOWED", command, "Explicitly allowed")
                return {
                    "allowed": True,
                    "requires_approval": False,
                    "reason": "Explicitly allowed"
                }

        # Check auto-approve patterns
        for pattern in self.policy.auto_approve_patterns:
            if command.startswith(pattern):
                self._audit("AUTO_APPROVED", command, f"Matches auto-approve pattern: {pattern}")
                return {
                    "allowed": True,
                    "requires_approval": False,
                    "reason": f"Auto-approved via pattern: {pattern}"
                }

        # Check if requires explicit approval
        for approval_cmd in self.policy.require_approval:
            if approval_cmd in command:
                self._audit("REQUIRES_APPROVAL", command, f"Requires approval: {approval_cmd}")
                return {
                    "allowed": True,
                    "requires_approval": True,
                    "reason": f"Requires explicit approval: {approval_cmd}"
                }

        # Default behavior based on mode
        if self.policy.mode == PermissionMode.SAFE:
            self._audit("REQUIRES_APPROVAL", command, "SAFE mode requires approval for all unlisted commands")
            return {
                "allowed": True,
                "requires_approval": True,
                "reason": "SAFE mode: requires approval"
            }
        elif self.policy.mode == PermissionMode.AUTO:
            self._audit("AUTO_APPROVED", command, "AUTO mode: auto-approved")
            return {
                "allowed": True,
                "requires_approval": False,
                "reason": "AUTO mode: auto-approved"
            }
        elif self.policy.mode == PermissionMode.SANDBOX:
            self._audit("AUTO_APPROVED", command, "SANDBOX mode: auto-approved in isolated environment")
            return {
                "allowed": True,
                "requires_approval": False,
                "reason": "SANDBOX mode: auto-approved (isolated)"
            }

        self._audit("REQUIRES_APPROVAL", command, "Default fallback")
        return {
            "allowed": True,
            "requires_approval": True,
            "reason": "Default: requires approval"
        }

    def check_dangerous_action(self, action: str) -> Dict[str, Any]:
        """Check if a dangerous action is permitted."""
        if action not in self.policy.dangerous_actions:
            return {"allowed": True, "reason": "Not classified as dangerous"}

        if self.policy.mode == PermissionMode.SAFE:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": f"SAFE mode blocks dangerous action: {action}"
            }
        elif self.policy.mode == PermissionMode.AUTO:
            return {
                "allowed": True,
                "requires_approval": True,
                "reason": f"AUTO mode allows but requires approval: {action}"
            }
        elif self.policy.mode == PermissionMode.SANDBOX:
            return {
                "allowed": True,
                "requires_approval": False,
                "reason": f"SANDBOX mode allows in isolation: {action}"
            }

        return {"allowed": False, "reason": "Unknown mode"}

    def _audit(self, decision: str, command: str, reason: str):
        """Log permission decision for audit trail."""
        self._audit_log.append({
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "decision": decision,
            "command": command,
            "reason": reason,
            "mode": self.policy.mode.value
        })

    def get_audit_log(self) -> List[Dict]:
        """Get permission audit log."""
        return self._audit_log.copy()

    def create_sandbox_config(self) -> Dict[str, Any]:
        """Create documented SANDBOX mode launch configuration."""
        return {
            "mode": "SANDBOX",
            "description": "Isolated disposable environment for broad automatic execution",
            "requirements": [
                "Docker or container runtime available",
                "Network isolation configured",
                "Ephemeral filesystem",
                "No access to host credentials"
            ],
            "launch_command": "docker run --rm -it --network none -v $(pwd):/workspace phantom-engine:sandbox",
            "environment_variables": {
                "PHANTOM_MODE": "SANDBOX",
                "PHANTOM_SANDBOX": "1",
                "CLAUDE_CODE_PERMISSION_MODE": "bypass"
            },
            "warning": "SANDBOX mode uses Claude Code's supported permission-bypass mode. Only enable when explicitly authorized by user."
        }


def get_default_policy() -> PermissionPolicy:
    """Get the default permission policy."""
    return PermissionPolicy()


if __name__ == "__main__":
    import sys
    pm = PermissionManager()

    if len(sys.argv) < 2:
        print("Usage: python permission_manager.py <command> [args...]")
        print("Commands: check <command>, mode <SAFE|AUTO|SANDBOX>, audit, sandbox-config")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "check":
        command = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        result = pm.check_command(command)
        print(json.dumps(result, indent=2))
    elif cmd == "mode":
        if len(sys.argv) > 2:
            mode = PermissionMode(sys.argv[2].upper())
            pm.set_mode(mode)
            print(f"Mode set to: {mode.value}")
        else:
            print(f"Current mode: {pm.get_mode().value}")
    elif cmd == "audit":
        print(json.dumps(pm.get_audit_log(), indent=2))
    elif cmd == "sandbox-config":
        print(json.dumps(pm.create_sandbox_config(), indent=2))
    else:
        print(f"Unknown command: {cmd}")