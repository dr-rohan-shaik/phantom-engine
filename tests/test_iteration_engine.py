"""
Tests for Phantom Engine Iteration Engine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scripts.iteration_engine import (
    IterationEngine,
    Phase,
    PhaseHandler,
    IterationResult,
    create_default_engine,
    AuditHandler,
    InvestigateHandler,
    PrioritizeHandler,
    FixHandler,
    TestHandler,
    ReviewHandler,
    LogHandler
)
from scripts.state_manager import StateManager, PhantomState


class MockStateManager:
    """Mock state manager for testing."""

    def __init__(self, tmp_path):
        self.state = PhantomState(active=True, max_iterations=3, task="Test task")
        self.phantom_dir = tmp_path / ".phantom"
        self.phantom_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        return self.state

    def save(self, state):
        self.state = state

    def initialize(self, task: str, mode: str = "AUTO", max_iterations: int = 10, execution_budget: int = 1000):
        self.state = PhantomState(
            active=True,
            mode=mode,
            iteration=0,
            max_iterations=max_iterations,
            task=task,
            phase="initializing",
            execution_budget=execution_budget
        )
        return self.state

    def can_continue(self):
        return self.state.active and not self.state.stop_requested and \
               self.state.iteration < self.state.max_iterations and \
               not self.state.verification_complete

    def update_phase(self, phase):
        self.state.phase = phase

    def increment_iteration(self):
        self.state.iteration += 1
        self.state.budget_used += 1

    def request_stop(self):
        self.state.stop_requested = True

    def add_error(self, error):
        self.state.errors.append(error)

    def add_warning(self, warning):
        self.state.warnings.append(warning)

    def deactivate(self):
        self.state.active = False

    def get_status_summary(self):
        return {
            "active": self.state.active,
            "iteration": self.state.iteration,
            "phase": self.state.phase
        }


class TestPhaseHandler:
    """Test PhaseHandler abstract base class."""

    def test_abstract_properties(self):
        """Test that PhaseHandler requires phase property."""
        with pytest.raises(TypeError):
            PhaseHandler()


class TestAuditHandler:
    """Test AuditHandler."""

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test audit handler execution."""
        handler = AuditHandler()
        state = PhantomState()
        context = {"iteration": 1}

        result = await handler.execute(state, context)

        assert result.success is True
        assert result.phase == Phase.AUDIT
        assert result.iteration == 1
        assert len(result.actions_taken) > 0


class TestInvestigateHandler:
    """Test InvestigateHandler."""

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test investigate handler execution."""
        handler = InvestigateHandler()
        state = PhantomState()
        context = {"iteration": 1}

        result = await handler.execute(state, context)

        assert result.success is True
        assert result.phase == Phase.INVESTIGATE


class TestIterationEngine:
    """Test IterationEngine."""

    @pytest.fixture
    def mock_state_manager(self, tmp_path):
        return MockStateManager(tmp_path)

    @pytest.fixture
    def engine(self, mock_state_manager):
        return create_default_engine(mock_state_manager, max_iterations=3)

    def test_register_handler(self, engine):
        """Test handler registration."""
        assert Phase.AUDIT in engine.phase_handlers
        assert Phase.INVESTIGATE in engine.phase_handlers
        assert Phase.PRIORITIZE in engine.phase_handlers
        assert Phase.FIX in engine.phase_handlers
        assert Phase.TEST in engine.phase_handlers
        assert Phase.REVIEW in engine.phase_handlers
        assert Phase.LOG in engine.phase_handlers

    def test_get_handler(self, engine):
        """Test getting handler for phase."""
        handler = engine.get_handler(Phase.AUDIT)
        assert handler is not None
        assert isinstance(handler, AuditHandler)

        handler = engine.get_handler(Phase.INVESTIGATE)
        assert isinstance(handler, InvestigateHandler)

        # Non-existent phase
        handler = engine.get_handler(Phase.DEPLOY)
        assert handler is None

    def test_phase_order(self, engine):
        """Test phase execution order."""
        order = engine._get_phase_order()
        expected = [
            Phase.AUDIT,
            Phase.INVESTIGATE,
            Phase.PRIORITIZE,
            Phase.FIX,
            Phase.TEST,
            Phase.REVIEW,
            Phase.LOG
        ]
        assert order == expected

    @pytest.mark.asyncio
    async def test_run_iteration(self, engine, mock_state_manager):
        """Test running a single iteration."""
        state = mock_state_manager.load()

        result = await engine.run_iteration(state)

        assert result.iteration == 1
        assert result.success is True
        assert result.phase == Phase.LOG
        assert len(result.actions_taken) > 0

    @pytest.mark.asyncio
    async def test_run_iteration_with_stop_request(self, engine, mock_state_manager):
        """Test iteration stops when stop requested."""
        mock_state_manager.state.stop_requested = True

        result = await engine.run_iteration(mock_state_manager.load())

        # Should still run but stop after first check
        assert result.iteration == 1

    @pytest.mark.asyncio
    async def test_run_loop(self, engine, mock_state_manager):
        """Test running the full loop."""
        result = await engine.run("Test task")

        assert "success" in result
        assert "iterations_completed" in result
        assert mock_state_manager.state.iteration > 0


class TestCreateDefaultEngine:
    """Test create_default_engine factory function."""

    def test_creates_engine_with_handlers(self, tmp_path):
        """Test that factory creates engine with all handlers."""
        mock_sm = MockStateManager(tmp_path)
        engine = create_default_engine(mock_sm)

        assert isinstance(engine, IterationEngine)
        assert len(engine.phase_handlers) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])