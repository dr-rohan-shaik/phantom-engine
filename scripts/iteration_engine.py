"""
Phantom Engine Iteration Engine
Core loop controller for the autonomous engineering cycle.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from scripts.state_manager import PhantomState, StateManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Phase(Enum):
    """Execution phases in the engineering cycle."""
    INITIALIZING = "initializing"
    AUDIT = "audit"
    INVESTIGATE = "investigate"
    PRIORITIZE = "prioritize"
    FIX = "fix"
    TEST = "test"
    REVIEW = "review"
    LOG = "log"
    DEPLOY = "deploy"
    VERIFY = "verify"
    COMPLETE = "complete"
    ERROR = "error"
    IDLE = "idle"


@dataclass
class IterationResult:
    """Result of a single iteration."""
    iteration: int
    phase: Phase
    success: bool
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    findings: List[Dict[str, Any]] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class PhaseHandler(ABC):
    """Abstract base class for phase handlers."""

    @property
    @abstractmethod
    def phase(self) -> Phase:
        """The phase this handler manages."""
        pass

    @abstractmethod
    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Execute the phase logic."""
        pass


class IterationEngine:
    """
    Core iteration engine for the Phantom Engine autonomous loop.
    Manages the AUDIT → INVESTIGATE → PRIORITIZE → FIX → TEST → REVIEW → LOG cycle.
    """

    def __init__(
        self,
        state_manager: StateManager,
        max_iterations: int = 10,
        max_runtime_seconds: int = 3600,
        permission_mode: str = "AUTO"
    ):
        self.state_manager = state_manager
        self.max_iterations = max_iterations
        self.max_runtime_seconds = max_runtime_seconds
        self.permission_mode = permission_mode
        self.phase_handlers: Dict[Phase, PhaseHandler] = {}
        self.start_time: Optional[float] = None
        self._running = False
        self._stop_event = asyncio.Event()

    def register_handler(self, handler: PhaseHandler):
        """Register a phase handler."""
        self.phase_handlers[handler.phase] = handler
        logger.info(f"Registered handler for phase: {handler.phase.value}")

    def get_handler(self, phase: Phase) -> Optional[PhaseHandler]:
        """Get handler for a phase."""
        return self.phase_handlers.get(phase)

    def _get_phase_order(self) -> List[Phase]:
        """Get the standard phase execution order."""
        return [
            Phase.AUDIT,
            Phase.INVESTIGATE,
            Phase.PRIORITIZE,
            Phase.FIX,
            Phase.TEST,
            Phase.REVIEW,
            Phase.LOG,
        ]

    async def run_iteration(self, state: PhantomState) -> IterationResult:
        """Run a single iteration through all phases."""
        iteration_start = time.time()
        iteration = state.iteration + 1
        all_findings = []
        all_actions = []
        all_errors = []

        self.state_manager.update_phase(Phase.AUDIT.value)

        for phase in self._get_phase_order():
            if not self.state_manager.can_continue() or self._stop_event.is_set():
                break

            handler = self.get_handler(phase)
            if not handler:
                logger.warning(f"No handler registered for phase: {phase.value}")
                continue

            self.state_manager.update_phase(phase.value)
            logger.info(f"Iteration {iteration}: Starting phase {phase.value}")

            phase_start = time.time()
            try:
                result = await handler.execute(state, {
                    "iteration": iteration,
                    "findings_so_far": all_findings,
                    "actions_so_far": all_actions,
                    "permission_mode": self.permission_mode
                })

                phase_duration = time.time() - phase_start
                result.duration_seconds = phase_duration
                result.iteration = iteration

                if result.success:
                    all_findings.extend(result.findings)
                    all_actions.extend(result.actions_taken)
                    logger.info(f"Iteration {iteration}: Phase {phase.value} completed successfully")
                else:
                    all_errors.extend(result.errors)
                    logger.error(f"Iteration {iteration}: Phase {phase.value} failed: {result.errors}")

                # Check if we should stop after this phase
                if not self.state_manager.can_continue():
                    break

            except Exception as e:
                logger.exception(f"Iteration {iteration}: Phase {phase.value} raised exception")
                all_errors.append(f"{phase.value}: {str(e)}")

        # Log phase
        self.state_manager.update_phase(Phase.LOG.value)
        await self._log_iteration(iteration, all_findings, all_actions, all_errors)

        iteration_duration = time.time() - iteration_start

        return IterationResult(
            iteration=iteration,
            phase=Phase.LOG,
            success=len(all_errors) == 0,
            started_at=datetime.fromtimestamp(iteration_start).isoformat(),
            completed_at=datetime.now().isoformat(),
            duration_seconds=iteration_duration,
            findings=all_findings,
            actions_taken=all_actions,
            errors=all_errors
        )

    async def _log_iteration(
        self,
        iteration: int,
        findings: List[Dict[str, Any]],
        actions: List[str],
        errors: List[str]
    ):
        """Log iteration results to iteration-log.md."""
        log_entry = f"""
## Iteration {iteration} - {datetime.now().isoformat()}

### Findings
{json.dumps(findings, indent=2) if findings else "None"}

### Actions Taken
{chr(10).join(f"- {a}" for a in actions) if actions else "None"}

### Errors
{chr(10).join(f"- {e}" for e in errors) if errors else "None"}

---
"""
        log_file = self.state_manager.phantom_dir / "iteration-log.md"
        with open(log_file, "a") as f:
            f.write(log_entry)

    async def run(self, initial_task: str) -> Dict[str, Any]:
        """Run the complete autonomous engineering loop."""
        logger.info(f"Starting Phantom Engine with task: {initial_task}")

        # Initialize state
        state = self.state_manager.initialize(
            task=initial_task,
            mode=self.permission_mode,
            max_iterations=self.max_iterations
        )

        self.start_time = time.time()
        self._running = True

        try:
            while self.state_manager.can_continue() and not self._stop_event.is_set():
                # Check runtime limit
                if self.start_time and (time.time() - self.start_time) > self.max_runtime_seconds:
                    logger.warning("Max runtime exceeded")
                    self.state_manager.add_warning("Max runtime exceeded")
                    break

                # Run iteration
                result = await self.run_iteration(state)

                # Update state
                self.state_manager.increment_iteration()
                state = self.state_manager.load()

                # Check completion criteria
                if result.success and state.verification_complete:
                    logger.info("Verification complete, stopping loop")
                    break

                # Small delay between iterations
                await asyncio.sleep(1)

            # Final phase
            self.state_manager.update_phase(Phase.COMPLETE.value)
            final_state = self.state_manager.load()

            return {
                "success": final_state.verification_complete,
                "iterations_completed": final_state.iteration,
                "final_phase": final_state.phase,
                "errors": final_state.errors,
                "warnings": final_state.warnings
            }

        except Exception as e:
            logger.exception("Engine crashed")
            self.state_manager.update_phase(Phase.ERROR.value)
            self.state_manager.add_error(f"Engine crash: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._running = False
            self.state_manager.deactivate()

    def request_stop(self):
        """Request graceful stop."""
        logger.info("Stop requested")
        self._stop_event.set()
        self.state_manager.request_stop()

    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running


# Default phase handlers (stubs for now)

class AuditHandler(PhaseHandler):
    """Repository audit phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.AUDIT

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Audit the repository for issues."""
        findings = []
        actions = ["Repository audit initiated"]

        # This would be implemented with actual repository analysis
        # For now, return a basic result
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            findings=findings,
            actions_taken=actions
        )


class InvestigateHandler(PhaseHandler):
    """Investigation phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.INVESTIGATE

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Investigate identified issues."""
        actions = ["Root cause analysis initiated"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


class PrioritizeHandler(PhaseHandler):
    """Prioritization phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.PRIORITIZE

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Prioritize fixes."""
        actions = ["Prioritization completed"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


class FixHandler(PhaseHandler):
    """Fix implementation phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.FIX

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Implement fixes."""
        actions = ["Fixes implemented"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


class TestHandler(PhaseHandler):
    """Testing phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.TEST

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Run tests."""
        actions = ["Tests executed"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


class ReviewHandler(PhaseHandler):
    """Code review phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.REVIEW

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Review changes."""
        actions = ["Code review completed"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


class LogHandler(PhaseHandler):
    """Logging phase handler."""

    @property
    def phase(self) -> Phase:
        return Phase.LOG

    async def execute(self, state: PhantomState, context: Dict[str, Any]) -> IterationResult:
        """Log iteration results."""
        actions = ["Iteration logged"]
        return IterationResult(
            iteration=context.get("iteration", 0),
            phase=self.phase,
            success=True,
            started_at=datetime.now().isoformat(),
            actions_taken=actions
        )


def create_default_engine(
    state_manager: StateManager,
    max_iterations: int = 10,
    max_runtime_seconds: int = 3600,
    permission_mode: str = "AUTO"
) -> IterationEngine:
    """Create an iteration engine with default handlers."""
    engine = IterationEngine(state_manager, max_iterations, max_runtime_seconds, permission_mode)

    engine.register_handler(AuditHandler())
    engine.register_handler(InvestigateHandler())
    engine.register_handler(PrioritizeHandler())
    engine.register_handler(FixHandler())
    engine.register_handler(TestHandler())
    engine.register_handler(ReviewHandler())
    engine.register_handler(LogHandler())

    return engine


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python iteration_engine.py <command> [args...]")
        sys.exit(1)

    sm = StateManager()
    engine = create_default_engine(sm)

    cmd = sys.argv[1]
    if cmd == "run":
        task = sys.argv[2] if len(sys.argv) > 2 else "Default task"
        result = asyncio.run(engine.run(task))
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {cmd}")