#!/usr/bin/env python3
"""
Phantom Engine Stop Guard Hook
Prevents Claude from stopping while the autonomous loop is active.
"""

import json
import sys
from pathlib import Path

def main():
    """Check if Phantom Engine loop is active and should continue."""
    phantom_dir = Path.cwd() / ".phantom"
    state_file = phantom_dir / "state.json"
    stop_file = phantom_dir / "STOP"

    # Check if stop file exists (explicit user request)
    if stop_file.exists():
        # Allow stop if explicitly requested
        print(json.dumps({
            "allow_stop": True,
            "reason": "STOP file present - explicit stop requested"
        }))
        return 0

    # Load state
    if not state_file.exists():
        # No active engine, allow stop
        print(json.dumps({
            "allow_stop": True,
            "reason": "No active Phantom Engine state"
        }))
        return 0

    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception:
        print(json.dumps({
            "allow_stop": True,
            "reason": "Could not read state file"
        }))
        return 0

    # Check if engine is active
    if not state.get("active", False):
        print(json.dumps({
            "allow_stop": True,
            "reason": "Phantom Engine not active"
        }))
        return 0

    # Check if stop was requested via state
    if state.get("stop_requested", False):
        print(json.dumps({
            "allow_stop": True,
            "reason": "Stop requested in state"
        }))
        return 0

    # Check iteration limits
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    if iteration >= max_iterations:
        print(json.dumps({
            "allow_stop": True,
            "reason": f"Max iterations reached ({iteration}/{max_iterations})"
        }))
        return 0

    # Check budget
    budget_used = state.get("budget_used", 0)
    execution_budget = state.get("execution_budget", 1000)
    if budget_used >= execution_budget:
        print(json.dumps({
            "allow_stop": True,
            "reason": f"Execution budget exhausted ({budget_used}/{execution_budget})"
        }))
        return 0

    # Check verification complete
    if state.get("verification_complete", False):
        print(json.dumps({
            "allow_stop": True,
            "reason": "Verification complete"
        }))
        return 0

    # Engine is active and should continue
    phase = state.get("phase", "unknown")
    task = state.get("task", "Unknown task")

    print(json.dumps({
        "allow_stop": False,
        "reason": f"Phantom Engine active: iteration {iteration}/{max_iterations}, phase '{phase}', task: '{task[:50]}...'",
        "metadata": {
            "iteration": iteration,
            "max_iterations": max_iterations,
            "phase": phase,
            "task": task,
            "budget_used": budget_used,
            "execution_budget": execution_budget
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())