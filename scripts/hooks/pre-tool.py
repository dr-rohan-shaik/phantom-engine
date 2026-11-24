#!/usr/bin/env python3
"""
Phantom Engine Pre-Tool Hook
Validates tool use against permission policy.
"""

import json
import sys
from pathlib import Path

def main():
    """Validate tool use before execution."""
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"allow": True, "reason": "Could not parse input"}))
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Load permission policy
    phantom_dir = Path.cwd() / ".phantom"
    perm_file = phantom_dir / "permissions.json"

    if not perm_file.exists():
        # No policy, allow by default
        print(json.dumps({"allow": True, "reason": "No permission policy configured"}))
        return 0

    try:
        with open(perm_file) as f:
            policy = json.load(f)
    except Exception:
        print(json.dumps({"allow": True, "reason": "Could not read permission policy"}))
        return 0

    mode = policy.get("mode", "AUTO")

    # In SAFE mode, require approval for all file modifications
    if mode == "SAFE":
        if tool_name in ("Write", "Edit", "MultiEdit", "Bash"):
            print(json.dumps({
                "allow": False,
                "reason": f"SAFE mode requires approval for {tool_name}",
                "requires_approval": True
            }))
            return 0

    # Check blocked patterns
    blocked = policy.get("blocked_commands", [])
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for pattern in blocked:
            if pattern in command:
                print(json.dumps({
                    "allow": False,
                    "reason": f"Command matches blocked pattern: {pattern}",
                    "requires_approval": False
                }))
                return 0

    # Allow by default
    print(json.dumps({"allow": True, "reason": "Allowed by permission policy"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())