#!/usr/bin/env python3
"""
Phantom Engine Session Guard Hook
Restores Phantom Engine state on session start.
"""

import json
import sys
from pathlib import Path

def main():
    """Restore Phantom Engine state on session start."""
    phantom_dir = Path.cwd() / ".phantom"
    state_file = phantom_dir / "state.json"

    if not state_file.exists():
        # No previous state
        print(json.dumps({
            "restored": False,
            "reason": "No previous state found"
        }))
        return 0

    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception as e:
        print(json.dumps({
            "restored": False,
            "reason": f"Could not read state: {e}"
        }))
        return 0

    # Check if there was an active session
    if not state.get("active", False):
        print(json.dumps({
            "restored": False,
            "reason": "No active session in previous state"
        }))
        return 0

    # Check if task was completed
    if state.get("verification_complete", False):
        print(json.dumps({
            "restored": False,
            "reason": "Previous task was completed"
        }))
        return 0

    # Check if stop was requested
    if state.get("stop_requested", False):
        print(json.dumps({
            "restored": False,
            "reason": "Stop was requested in previous session"
        }))
        return 0

    # There's an incomplete task - offer to resume
    task = state.get("task", "Unknown task")
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    phase = state.get("phase", "unknown")

    print(json.dumps({
        "restored": True,
        "message": f"Resuming Phantom Engine task: '{task}' (iteration {iteration}/{max_iterations}, phase: {phase})",
        "state": {
            "task": task,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "phase": phase,
            "mode": state.get("mode", "AUTO"),
            "repository_path": state.get("repository_path", str(Path.cwd())),
            "git_branch": state.get("git_branch", "")
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())