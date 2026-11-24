"""
Tests for Phantom Engine State Manager
"""

import json
import tempfile
import pytest
from pathlib import Path

from scripts.state_manager import StateManager, PhantomState


class TestStateManager:
    """Test cases for StateManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create StateManager with temp directory."""
        return StateManager(phantom_dir=temp_dir / ".phantom")

    def test_initial_state(self, state_manager):
        """Test initial state is empty."""
        state = state_manager.load()
        assert state.active is False
        assert state.mode == "AUTO"
        assert state.iteration == 0
        assert state.task == ""

    def test_initialize_state(self, state_manager):
        """Test state initialization."""
        state = state_manager.initialize(
            task="Test task",
            mode="AUTO",
            max_iterations=5,
            execution_budget=100
        )

        assert state.active is True
        assert state.mode == "AUTO"
        assert state.max_iterations == 5
        assert state.task == "Test task"
        assert state.execution_budget == 100
        assert state.started_at is not None

    def test_save_and_load(self, state_manager):
        """Test state persistence."""
        state_manager.initialize(task="Persist test")
        state = state_manager.load()

        assert state.task == "Persist test"
        assert state.active is True

    def test_increment_iteration(self, state_manager):
        """Test iteration counter increment."""
        state_manager.initialize(task="Iteration test")

        state_manager.increment_iteration()
        state = state_manager.load()
        assert state.iteration == 1
        assert state.budget_used == 1

        state_manager.increment_iteration()
        state = state_manager.load()
        assert state.iteration == 2
        assert state.budget_used == 2

    def test_update_phase(self, state_manager):
        """Test phase update."""
        state_manager.initialize(task="Phase test")
        state_manager.update_phase("testing")

        state = state_manager.load()
        assert state.phase == "testing"

    def test_request_stop(self, state_manager):
        """Test stop request."""
        state_manager.initialize(task="Stop test")
        state_manager.request_stop()

        state = state_manager.load()
        assert state.stop_requested is True

    def test_can_continue(self, state_manager):
        """Test continuation logic."""
        state_manager.initialize(
            task="Continue test",
            max_iterations=2,
            execution_budget=5
        )

        # Should continue initially
        assert state_manager.can_continue() is True

        # After 2 iterations, should stop
        state_manager.increment_iteration()
        state_manager.increment_iteration()
        assert state_manager.can_continue() is False

    def test_add_error_warning(self, state_manager):
        """Test error and warning tracking."""
        state_manager.initialize(task="Error test")

        state_manager.add_error("Test error")
        state_manager.add_warning("Test warning")

        state = state_manager.load()
        assert len(state.errors) == 1
        assert "Test error" in state.errors[0]
        assert len(state.warnings) == 1
        assert "Test warning" in state.warnings[0]

    def test_deactivate(self, state_manager):
        """Test deactivation."""
        state_manager.initialize(task="Deactivate test")
        state_manager.deactivate()

        state = state_manager.load()
        assert state.active is False

    def test_atomic_write(self, state_manager):
        """Test atomic write doesn't corrupt state."""
        state_manager.initialize(task="Atomic test")

        # Simulate concurrent writes
        for i in range(10):
            state_manager.update_phase(f"phase-{i}")

        state = state_manager.load()
        assert state.phase == "phase-9"

    def test_schema_validation(self, state_manager):
        """Test that extra fields in JSON don't break loading."""
        # Write state with extra field
        state_file = state_manager.state_file
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({
                "active": True,
                "mode": "AUTO",
                "iteration": 1,
                "max_iterations": 10,
                "task": "Schema test",
                "phase": "idle",
                "stop_requested": False,
                "verification_complete": False,
                "deployment_status": "not_started",
                "extra_field": "should be ignored"
            }, f)

        state = state_manager.load()
        assert state.task == "Schema test"
        assert state.iteration == 1


class TestPhantomState:
    """Test PhantomState dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        state = PhantomState(
            active=True,
            mode="AUTO",
            iteration=5,
            task="Test"
        )
        data = state.to_dict()

        assert data["active"] is True
        assert data["mode"] == "AUTO"
        assert data["iteration"] == 5
        assert data["task"] == "Test"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "active": True,
            "mode": "SAFE",
            "iteration": 3,
            "max_iterations": 10,
            "task": "From dict",
            "phase": "testing",
            "stop_requested": False,
            "verification_complete": False,
            "deployment_status": "not_started",
            "started_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "repository_path": "/test",
            "git_branch": "main",
            "execution_budget": 100,
            "budget_used": 3,
            "errors": [],
            "warnings": [],
            "metadata": {}
        }

        state = PhantomState.from_dict(data)
        assert state.mode == "SAFE"
        assert state.iteration == 3
        assert state.task == "From dict"
        assert state.git_branch == "main"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])