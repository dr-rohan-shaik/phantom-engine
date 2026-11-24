#!/usr/bin/env python3
"""
Phantom Engine Post-Tool Hook
Logs tool execution and updates state.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    """Log tool execution after completion."""
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_result = input_data.get("tool_result", {})

    # Log to iteration log
    phantom_dir = Path.cwd() / ".phantom"
    log_file = phantom_dir / "tool-execution.log"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "input_summary": summarize_input(tool_name, tool_input),
        "success": not tool_result.get("isError", False)
    }

    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

    return 0


def summarize_input(tool_name: str, tool_input: dict) -> str:
    """Create a summary of tool input for logging."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:100] + ("..." if len(cmd) > 100 else "")
    elif tool_name in ("Write", "Edit", "MultiEdit"):
        path = tool_input.get("file_path", "")
        return f"{tool_name}: {path}"
    elif tool_name == "Read":
        path = tool_input.get("file_path", "")
        return f"Read: {path}"
    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"Glob: {pattern}"
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"Grep: {pattern}"
    elif tool_name == "Task":
        desc = tool_input.get("description", "")
        return f"Task: {desc[:50]}"
    else:
        return tool_name


if __name__ == "__main__":
    sys.exit(main())