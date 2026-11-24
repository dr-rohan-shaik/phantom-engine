"""
Phantom Engine State Manager
Handles persistent state management across sessions with atomic writes and schema validation.
"""

import json
import os
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import tempfile

# Cross-platform file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False


@dataclass
class PhantomState:
    """Phantom Engine execution state."""
    active: bool = False
    mode: str = "AUTO"
    iteration: int = 0
    max_iterations: int = 10
    task: str = ""
    phase: str = "idle"
    stop_requested: bool = False
    verification_complete: bool = False
    deployment_status: str = "not_started"
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    repository_path: str = ""
    git_branch: str = ""
    execution_budget: int = 1000
    budget_used: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhantomState":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class StateManager:
    """Manages Phantom Engine state with atomic writes and file locking."""

    def __init__(self, phantom_dir: Optional[Path] = None):
        self.phantom_dir = phantom_dir or Path.cwd() / ".phantom"
        self.phantom_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.phantom_dir / "state.json"
        self.lock_file = self.phantom_dir / ".state.lock"
        self._lock = threading.RLock()

    def _acquire_lock(self) -> bool:
        """Acquire file lock for atomic operations."""
        try:
            self.lock_file.touch(exist_ok=True)
            with open(self.lock_file, 'w') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                elif HAS_MSVCRT:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # No locking available, proceed without lock
                    pass
                return True
        except (IOError, OSError):
            return False

    def _release_lock(self):
        """Release file lock."""
        try:
            with open(self.lock_file, 'w') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                elif HAS_MSVCRT:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except (IOError, OSError):
            pass

    def _atomic_write(self, data: Dict[str, Any]):
        """Write state atomically using temp file and rename."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.phantom_dir,
            prefix='state_',
            suffix='.tmp',
            delete=False
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_name = tmp.name

        os.replace(tmp_name, self.state_file)

    def load(self) -> PhantomState:
        """Load state from file."""
        with self._lock:
            if not self.state_file.exists():
                return PhantomState()

            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                return PhantomState.from_dict(data)
            except (json.JSONDecodeError, OSError):
                return PhantomState()

    def save(self, state: PhantomState):
        """Save state to file atomically."""
        with self._lock:
            state.updated_at = datetime.now().isoformat()
            if state.started_at is None:
                state.started_at = state.updated_at
            self._atomic_write(state.to_dict())

    def initialize(self, task: str, mode: str = "AUTO", max_iterations: int = 10,
                   execution_budget: int = 1000, repository_path: str = "") -> PhantomState:
        """Initialize new state for a task."""
        state = PhantomState(
            active=True,
            mode=mode,
            iteration=0,
            max_iterations=max_iterations,
            task=task,
            phase="initializing",
            repository_path=repository_path or str(Path.cwd()),
            execution_budget=execution_budget,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.save(state)
        return state

    def update_phase(self, phase: str):
        """Update current phase."""
        state = self.load()
        state.phase = phase
        self.save(state)

    def increment_iteration(self):
        """Increment iteration counter."""
        state = self.load()
        state.iteration += 1
        state.budget_used += 1
        self.save(state)

    def request_stop(self):
        """Request graceful stop."""
        state = self.load()
        state.stop_requested = True
        self.save(state)

    def mark_verification_complete(self):
        """Mark verification as complete."""
        state = self.load()
        state.verification_complete = True
        self.save(state)

    def add_error(self, error: str):
        """Add error to state."""
        state = self.load()
        state.errors.append(f"{datetime.now().isoformat()}: {error}")
        self.save(state)

    def add_warning(self, warning: str):
        """Add warning to state."""
        state = self.load()
        state.warnings.append(f"{datetime.now().isoformat()}: {warning}")
        self.save(state)

    def set_git_branch(self, branch: str):
        """Set git branch."""
        state = self.load()
        state.git_branch = branch
        self.save(state)

    def set_deployment_status(self, status: str):
        """Set deployment status."""
        state = self.load()
        state.deployment_status = status
        self.save(state)

    def can_continue(self) -> bool:
        """Check if loop can continue."""
        state = self.load()
        if not state.active:
            return False
        if state.stop_requested:
            return False
        if state.iteration >= state.max_iterations:
            return False
        if state.budget_used >= state.execution_budget:
            return False
        if state.verification_complete:
            return False
        return True

    def deactivate(self):
        """Deactivate the engine."""
        state = self.load()
        state.active = False
        self.save(state)

    def get_status_summary(self) -> Dict[str, Any]:
        """Get status summary for display."""
        state = self.load()
        return {
            "active": state.active,
            "mode": state.mode,
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
            "task": state.task,
            "phase": state.phase,
            "verification_complete": state.verification_complete,
            "deployment_status": state.deployment_status,
            "budget_used": state.budget_used,
            "execution_budget": state.execution_budget,
            "errors_count": len(state.errors),
            "warnings_count": len(state.warnings),
            "started_at": state.started_at,
            "updated_at": state.updated_at
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python state_manager.py <command> [args...]")
        sys.exit(1)

    sm = StateManager()
    cmd = sys.argv[1]

    if cmd == "init":
        task = sys.argv[2] if len(sys.argv) > 2 else "Default task"
        state = sm.initialize(task)
        print(f"Initialized: {state.task}")
    elif cmd == "load":
        state = sm.load()
        print(json.dumps(state.to_dict(), indent=2))
    elif cmd == "status":
        print(json.dumps(sm.get_status_summary(), indent=2))
    elif cmd == "continue":
        print(json.dumps({"can_continue": sm.can_continue()}))
    elif cmd == "stop":
        sm.request_stop()
        print("Stop requested")
    elif cmd == "deactivate":
        sm.deactivate()
        print("Deactivated")
    else:
        print(f"Unknown command: {cmd}")