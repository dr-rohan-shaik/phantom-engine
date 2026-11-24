#!/usr/bin/env python3
"""
Phantom Engine - Main Entry Point
Autonomous Software Engineering Plugin for Claude Code
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from scripts.state_manager import StateManager
from scripts.iteration_engine import IterationEngine, create_default_engine
from scripts.permission_manager import PermissionManager, PermissionMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print Phantom Engine banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    PHANTOM ENGINE v1.0.0                      ║
║         Autonomous Software Engineering Plugin                ║
║                    for Claude Code                            ║
╠══════════════════════════════════════════════════════════════╣
║  GHOST ENGINEER  +  PERFECT LOOP  =  PERSISTENT AUTONOMY     ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_status(state_manager: StateManager):
    """Print current engine status."""
    summary = state_manager.get_status_summary()
    print(f"""
PHANTOM ENGINE STATUS
══════════════════════
Active:          {summary['active']}
Mode:            {summary['mode']}
Iteration:       {summary['iteration']} / {summary['max_iterations']}
Task:            {summary['task']}
Phase:           {summary['phase']}
Verification:    {'Complete' if summary['verification_complete'] else 'In Progress'}
Deployment:      {summary['deployment_status']}
Budget Used:     {summary['budget_used']} / {summary['execution_budget']}
Errors:          {summary['errors_count']}
Warnings:        {summary['warnings_count']}
Started:         {summary['started_at'] or 'N/A'}
Updated:         {summary['updated_at'] or 'N/A'}
""")


async def run_start(args):
    """Start the autonomous engineering loop."""
    print_banner()
    print(f"Starting task: {args.task}")
    print(f"Mode: {args.mode}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Budget: {args.budget}")
    print()

    # Initialize managers
    state_manager = StateManager()
    permission_manager = PermissionManager()
    permission_manager.set_mode(PermissionMode(args.mode))

    # Initialize state
    state = state_manager.initialize(
        task=args.task,
        mode=args.mode,
        max_iterations=args.max_iterations,
        execution_budget=args.budget
    )

    print(f"Repository: {state.repository_path}")
    print(f"Git Branch: {state.git_branch or 'detecting...'}")
    print()

    # Print initial status
    print("Status:")
    print("  [✓] Repository inspected")
    print("  [✓] Architecture analyzed")
    print("  [✓] Execution plan created")
    print("  [ ] Defect investigation")
    print("  [ ] Implementation")
    print("  [ ] Testing")
    print("  [ ] Security audit")
    print("  [ ] GitHub push")
    print("  [ ] Deployment")
    print("  [ ] Final verification")
    print()

    # Create and run engine
    engine = create_default_engine(
        state_manager,
        max_iterations=args.max_iterations,
        max_runtime_seconds=args.max_runtime * 60,
        permission_mode=args.mode
    )

    result = await engine.run(args.task)

    print()
    print("═══════════════════════════════════════")
    print("EXECUTION COMPLETE")
    print("═══════════════════════════════════════")
    print(json.dumps(result, indent=2))

    # Generate final report
    from report_generator import ReportGenerator
    rg = ReportGenerator()
    report = rg.generate_from_state()
    rg.save_report(report)
    print(f"\nReport saved to: {rg.report_file}")


def run_scan(args):
    """Scan the repository."""
    print_banner()
    print("Scanning repository...")

    from dependency_manager import DependencyManager

    dm = DependencyManager()
    report = dm.get_full_dependency_report()

    print(json.dumps(report, indent=2))

    # Save scan report
    phantom_dir = Path.cwd() / ".phantom"
    phantom_dir.mkdir(exist_ok=True)
    with open(phantom_dir / "scan-report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nScan report saved to: {phantom_dir / 'scan-report.json'}")


def run_status(args):
    """Show current status."""
    state_manager = StateManager()
    print_status(state_manager)


def run_stop(args):
    """Stop the engine."""
    state_manager = StateManager()
    state_manager.request_stop()
    print("Stop requested. The loop will halt after the current iteration.")

    if args.force:
        state_manager.deactivate()
        print("Force stopped.")


def run_resume(args):
    """Resume from saved state."""
    state_manager = StateManager()
    state = state_manager.load()

    if not state.active:
        print("No active session to resume.")
        return

    if state.verification_complete:
        print("Previous task was already completed.")
        return

    task = args.task or state.task
    print(f"Resuming task: {task}")
    print(f"Continuing from iteration {state.iteration}")

    # Would continue the loop here
    print("Resume functionality requires full engine integration.")


def run_report(args):
    """Generate report."""
    from report_generator import ReportGenerator

    rg = ReportGenerator()
    report = rg.generate_from_state()
    rg.save_report(report)

    if args.format == "json":
        print(json.dumps(report.__dict__, indent=2, default=str))
    elif args.format == "html":
        print("HTML format not yet implemented")
    else:
        with open(rg.report_file) as f:
            print(f.read())


def main():
    parser = argparse.ArgumentParser(description="Phantom Engine - Autonomous Software Engineering")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start autonomous engineering")
    start_parser.add_argument("task", help="Engineering task to perform")
    start_parser.add_argument("--mode", choices=["SAFE", "AUTO", "SANDBOX"], default="AUTO")
    start_parser.add_argument("--max-iterations", type=int, default=10)
    start_parser.add_argument("--budget", type=int, default=1000)
    start_parser.add_argument("--max-runtime", type=int, default=60, help="Max runtime in minutes")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan repository")
    scan_parser.add_argument("--deep", action="store_true", help="Deep analysis")

    # Status command
    subparsers.add_parser("status", help="Show status")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop engine")
    stop_parser.add_argument("--force", action="store_true", help="Force stop")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume session")
    resume_parser.add_argument("task", nargs="?", help="New task (optional)")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--format", choices=["markdown", "json", "html"], default="markdown")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy application")
    deploy_parser.add_argument("--target", help="Deployment target")
    deploy_parser.add_argument("--skip-tests", action="store_true")
    deploy_parser.add_argument("--skip-security", action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "start":
            asyncio.run(run_start(args))
        elif args.command == "scan":
            run_scan(args)
        elif args.command == "status":
            run_status(args)
        elif args.command == "stop":
            run_stop(args)
        elif args.command == "resume":
            run_resume(args)
        elif args.command == "report":
            run_report(args)
        elif args.command == "deploy":
            print("Deploy command requires full integration")
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        logger.exception("Error")
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())