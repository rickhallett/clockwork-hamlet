#!/usr/bin/env python3
"""
Autonomous Test Improvement Runner

Orchestrates sequential ralph-wiggum loops to implement each phase
of the test improvement plan with fail-safes and progress tracking.

Usage:
    python scripts/run-test-improvement.py
    python scripts/run-test-improvement.py --start-phase 3
    python scripts/run-test-improvement.py --dry-run
    python scripts/run-test-improvement.py --phase 2  # Run single phase only
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PhaseConfig:
    """Configuration for a single improvement phase."""

    number: int
    name: str
    prompt: str
    completion_promise: str
    verification_cmd: str
    max_iterations: int = 15
    timeout_minutes: int = 90


# Phase definitions - prompts are single-line to avoid shell escaping issues
PHASES = [
    PhaseConfig(
        number=1,
        name="Stabilize - Fix Flaky Tests",
        prompt="Implement Phase 1 of docs/test-improvement-plan.md. Fix the flaky test in test_actions.py by handling the boundary condition where relationship score is already at max. Update Pydantic schemas in backend/src/hamlet/api/schemas.py to use ConfigDict instead of inner Config class. Add pytest markers configuration to pyproject.toml. Run tests after each change. Work in backend/ directory.",
        completion_promise="uv run pytest in backend passes with 0 failures",
        verification_cmd="cd backend && uv run pytest --tb=short -q",
        max_iterations=10,
    ),
    PhaseConfig(
        number=2,
        name="Isolate - Database Isolation",
        prompt="Implement Phase 2 of docs/test-improvement-plan.md. Update tests/conftest.py to create isolated test databases per module using tempfile. Add transaction rollback pattern so each test starts fresh. Ensure tests can run in any order without state pollution. Run tests to verify. Work in backend/ directory.",
        completion_promise="uv run pytest in backend passes and tests are isolated",
        verification_cmd="cd backend && uv run pytest --tb=short -q",
        max_iterations=12,
    ),
    PhaseConfig(
        number=3,
        name="Categorize - Add Test Markers",
        prompt="Implement Phase 3 of docs/test-improvement-plan.md. Add pytest.mark.unit markers to fast isolated tests. Add pytest.mark.integration markers to tests that need full setup. Add pytest.mark.slow markers to tests over 1s. Verify with uv run pytest -m unit --collect-only. Work in backend/tests/ directory.",
        completion_promise="uv run pytest -m unit --collect-only shows marked tests",
        verification_cmd="cd backend && uv run pytest -m unit --collect-only",
        max_iterations=10,
    ),
    PhaseConfig(
        number=4,
        name="Expand - Add Integration Tests",
        prompt="Implement Phase 4 of docs/test-improvement-plan.md. Create tests/test_integration.py with end-to-end simulation tests. Add TestSimulationFlow class with async tests for simulation ticks. Create tests/test_api_contracts.py to verify API response schemas. Mark new tests with pytest.mark.integration and pytest.mark.slow. Run the new tests. Work in backend/ directory.",
        completion_promise="uv run pytest tests/test_integration.py tests/test_api_contracts.py passes",
        verification_cmd="cd backend && uv run pytest tests/test_integration.py tests/test_api_contracts.py --tb=short -q",
        max_iterations=15,
    ),
    PhaseConfig(
        number=5,
        name="Automate - Create Validation Command",
        prompt="Implement Phase 5 of docs/test-improvement-plan.md. Create .claude/commands/validate.md slash command for full validation. Add coverage configuration to pyproject.toml with fail_under=70. The validation workflow should run backend tests, backend lint, frontend build, frontend lint. Work from project root.",
        completion_promise="validate.md command file exists and coverage config is in pyproject.toml",
        verification_cmd="test -f .claude/commands/validate.md && grep -q 'fail_under' backend/pyproject.toml",
        max_iterations=8,
    ),
    PhaseConfig(
        number=6,
        name="Monitor - Add Performance Tests",
        prompt="Implement Phase 6 of docs/test-improvement-plan.md. Add test metrics tracking hook to tests/conftest.py. Create tests/test_performance.py with performance regression tests. Add tests for API endpoint response times with agent list under 100ms and events under 200ms. Mark performance tests with pytest.mark.slow. Run performance tests. Work in backend/ directory.",
        completion_promise="uv run pytest tests/test_performance.py passes",
        verification_cmd="cd backend && uv run pytest tests/test_performance.py --tb=short -q",
        max_iterations=10,
    ),
]


class ProgressTracker:
    """Tracks and persists progress across runs."""

    def __init__(self, project_root: Path):
        self.progress_file = project_root / "logs" / "test-improvement" / "progress.json"
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.progress_file.exists():
            return json.loads(self.progress_file.read_text())
        return {"phases": {}, "started_at": None, "last_updated": None}

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        self.progress_file.write_text(json.dumps(self.data, indent=2))

    def start_run(self):
        if not self.data["started_at"]:
            self.data["started_at"] = datetime.now().isoformat()
        self.save()

    def mark_phase_started(self, phase_num: int):
        self.data["phases"][str(phase_num)] = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
        }
        self.save()

    def mark_phase_completed(self, phase_num: int, success: bool):
        self.data["phases"][str(phase_num)].update(
            {
                "status": "completed" if success else "failed",
                "completed_at": datetime.now().isoformat(),
                "success": success,
            }
        )
        self.save()

    def get_last_successful_phase(self) -> int:
        """Returns the last phase that completed successfully."""
        last = 0
        for phase_str, info in self.data["phases"].items():
            if info.get("success"):
                last = max(last, int(phase_str))
        return last


class Logger:
    """Handles logging to file and console."""

    COLORS = {
        "red": "\033[0;31m",
        "green": "\033[0;32m",
        "yellow": "\033[1;33m",
        "blue": "\033[0;34m",
        "reset": "\033[0m",
    }

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"run_{timestamp}.log"

    def _log(self, level: str, msg: str, color: Optional[str] = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {msg}"

        # Write to file (no colors)
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")

        # Print to console (with colors)
        if color and sys.stdout.isatty():
            print(f"{self.COLORS.get(color, '')}{log_msg}{self.COLORS['reset']}")
        else:
            print(log_msg)

    def info(self, msg: str):
        self._log("INFO", msg)

    def error(self, msg: str):
        self._log("ERROR", msg, "red")

    def success(self, msg: str):
        self._log("SUCCESS", msg, "green")

    def warn(self, msg: str):
        self._log("WARN", msg, "yellow")

    def phase_header(self, phase_num: int, name: str):
        border = "═" * 60
        print(f"\n{self.COLORS['blue']}{border}{self.COLORS['reset']}")
        print(f"{self.COLORS['blue']}  PHASE {phase_num}: {name}{self.COLORS['reset']}")
        print(f"{self.COLORS['blue']}{border}{self.COLORS['reset']}\n")


def run_ralph_wiggum(
    phase: PhaseConfig,
    project_root: Path,
    logger: Logger,
    dry_run: bool = False,
) -> bool:
    """Execute a ralph-wiggum loop for a phase."""

    logger.info(f"Starting phase with max {phase.max_iterations} iterations")
    logger.info(f"Completion criteria: {phase.completion_promise}")

    if dry_run:
        logger.info("[DRY RUN] Would execute ralph-wiggum loop")
        logger.info(f"Prompt: {phase.prompt[:100]}...")
        return True

    # Build the command
    ralph_cmd = (
        f'/ralph-wiggum:ralph-loop "{phase.prompt}" '
        f'--max-iterations {phase.max_iterations} '
        f'--completion-promise "{phase.completion_promise}"'
    )

    cmd = ["claude", "--dangerously-skip-permissions", ralph_cmd]

    try:
        timeout_seconds = phase.timeout_minutes * 60
        result = subprocess.run(
            cmd,
            cwd=project_root,
            timeout=timeout_seconds,
            capture_output=False,  # Let output stream to terminal
        )
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logger.error(f"Phase timed out after {phase.timeout_minutes} minutes")
        return False
    except Exception as e:
        logger.error(f"Phase failed with error: {e}")
        return False


def verify_phase(phase: PhaseConfig, project_root: Path, logger: Logger) -> bool:
    """Verify a phase completed successfully."""
    logger.info(f"Verifying: {phase.verification_cmd}")

    try:
        result = subprocess.run(
            phase.verification_cmd,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.success(f"Phase {phase.number} verification passed")
            return True
        else:
            logger.warn(f"Verification output: {result.stderr or result.stdout}")
            return False

    except Exception as e:
        logger.warn(f"Verification failed: {e}")
        return False


def run_final_validation(project_root: Path, logger: Logger) -> bool:
    """Run final test suite validation."""
    logger.info("Running final validation...")

    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--tb=short", "-q"],
            cwd=project_root / "backend",
            timeout=300,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Final validation failed: {e}")
        return False


def print_summary(
    completed_phases: list[int],
    failed_phase: Optional[int],
    logger: Logger,
):
    """Print execution summary."""
    colors = Logger.COLORS

    print(f"\n{colors['blue']}{'═' * 60}{colors['reset']}")
    print(f"{colors['blue']}  EXECUTION SUMMARY{colors['reset']}")
    print(f"{colors['blue']}{'═' * 60}{colors['reset']}\n")

    if failed_phase is None:
        print(f"{colors['green']}All phases completed successfully!{colors['reset']}")
        for phase_num in completed_phases:
            print(f"  {colors['green']}✓{colors['reset']} Phase {phase_num}")
    else:
        print(f"{colors['red']}Execution stopped at phase {failed_phase}{colors['reset']}")
        for phase_num in completed_phases:
            print(f"  {colors['green']}✓{colors['reset']} Phase {phase_num}")
        print(f"  {colors['red']}✗{colors['reset']} Phase {failed_phase}")
        print(f"\n{colors['yellow']}To resume: python {__file__} --start-phase {failed_phase}{colors['reset']}")

    print(f"\nLog file: {logger.log_file}")


def main():
    parser = argparse.ArgumentParser(description="Run autonomous test improvements")
    parser.add_argument(
        "--start-phase",
        type=int,
        default=1,
        help="Phase to start from (default: 1)",
    )
    parser.add_argument(
        "--phase",
        type=int,
        help="Run only a specific phase",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last successful phase",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification between phases (rely on ralph-wiggum completion promise)",
    )
    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.resolve()
    log_dir = project_root / "logs" / "test-improvement"

    logger = Logger(log_dir)
    progress = ProgressTracker(project_root)

    logger.info(f"Project root: {project_root}")
    logger.info(f"Log file: {logger.log_file}")

    # Determine starting phase
    if args.resume:
        start_phase = progress.get_last_successful_phase() + 1
        logger.info(f"Resuming from phase {start_phase}")
    elif args.phase:
        start_phase = args.phase
    else:
        start_phase = args.start_phase

    # Filter phases to run
    if args.phase:
        phases_to_run = [p for p in PHASES if p.number == args.phase]
    else:
        phases_to_run = [p for p in PHASES if p.number >= start_phase]

    if not phases_to_run:
        logger.error(f"No phases to run (start_phase={start_phase})")
        return 1

    progress.start_run()

    # Execute phases
    completed_phases = []
    failed_phase = None

    for phase in phases_to_run:
        logger.phase_header(phase.number, phase.name)
        progress.mark_phase_started(phase.number)

        success = run_ralph_wiggum(phase, project_root, logger, args.dry_run)

        if success:
            # Verify the phase (unless skipped)
            if not args.dry_run and not args.no_verify:
                verify_phase(phase, project_root, logger)

            progress.mark_phase_completed(phase.number, True)
            completed_phases.append(phase.number)
            logger.success(f"Phase {phase.number} complete")

            # Brief pause between phases
            if phase != phases_to_run[-1]:
                time.sleep(2)
        else:
            progress.mark_phase_completed(phase.number, False)
            failed_phase = phase.number
            break

    # Final validation if all phases completed
    if failed_phase is None and not args.dry_run:
        run_final_validation(project_root, logger)

    print_summary(completed_phases, failed_phase, logger)

    return 0 if failed_phase is None else 1


if __name__ == "__main__":
    sys.exit(main())
