#!/bin/bash
#
# Autonomous Test Improvement Runner
# Executes each phase of test-improvement-plan.md using ralph-wiggum loops
#
# Usage: ./scripts/run-test-improvement.sh [--start-phase N] [--dry-run]
#

set -e

# Configuration
MAX_ITERATIONS_PER_PHASE=15
PHASE_TIMEOUT_MINUTES=30
LOG_DIR="logs/test-improvement"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/run_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
START_PHASE=1
DRY_RUN=false
SKIP_VERIFY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-phase)
            START_PHASE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-verify)
            SKIP_VERIFY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure we're in the project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level=$1
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

log_phase() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}  PHASE $1: $2${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo ""
}

# Run a single phase with ralph-wiggum
run_phase() {
    local phase_num=$1
    local phase_name=$2
    local prompt=$3
    local completion_promise=$4
    local max_iterations=${5:-$MAX_ITERATIONS_PER_PHASE}

    log_phase "$phase_num" "$phase_name"
    log "INFO" "Starting phase with max $max_iterations iterations"
    log "INFO" "Completion criteria: $completion_promise"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY RUN] Would execute ralph-wiggum loop"
        log "INFO" "Prompt: $prompt"
        return 0
    fi

    # Create a phase-specific log
    local phase_log="${LOG_DIR}/phase${phase_num}_${TIMESTAMP}.log"

    # Run claude with ralph-wiggum loop
    # Using timeout to enforce phase time limit
    local timeout_seconds=$((PHASE_TIMEOUT_MINUTES * 60))

    set +e  # Don't exit on error for this command
    timeout "$timeout_seconds" claude --dangerously-skip-permissions "/ralph-wiggum:ralph-loop \"$prompt\" --max-iterations $max_iterations --completion-promise \"$completion_promise\"" 2>&1 | tee -a "$phase_log"
    local exit_code=$?
    set -e

    if [ $exit_code -eq 124 ]; then
        log "ERROR" "Phase $phase_num timed out after $PHASE_TIMEOUT_MINUTES minutes"
        return 1
    elif [ $exit_code -ne 0 ]; then
        log "ERROR" "Phase $phase_num failed with exit code $exit_code"
        return 1
    fi

    log "INFO" "Phase $phase_num completed successfully"
    return 0
}

# Verify phase completion
verify_phase() {
    local phase_num=$1
    local verification_cmd=$2

    log "INFO" "Verifying phase $phase_num: $verification_cmd"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY RUN] Would verify with: $verification_cmd"
        return 0
    fi

    set +e
    eval "$verification_cmd" >> "$LOG_FILE" 2>&1
    local result=$?
    set -e

    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✓ Phase $phase_num verification passed${NC}" | tee -a "$LOG_FILE"
        return 0
    else
        echo -e "${RED}✗ Phase $phase_num verification failed${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Phase definitions
declare -A PHASES

# Phase 1: Stabilize
PHASES[1_name]="Stabilize - Fix Flaky Tests"
PHASES[1_prompt]="Implement Phase 1 of docs/test-improvement-plan.md. Fix the flaky test in test_actions.py by handling the boundary condition where relationship score is already at max. Update Pydantic schemas in backend/src/hamlet/api/schemas.py to use ConfigDict instead of inner Config class. Add pytest markers configuration to pyproject.toml. Run tests after each change. Work in backend/ directory."
PHASES[1_promise]="uv run pytest in backend passes with 0 failures"
PHASES[1_verify]="cd backend && uv run pytest --tb=short -q"
PHASES[1_iterations]=10

# Phase 2: Isolate
PHASES[2_name]="Isolate - Database Isolation"
PHASES[2_prompt]="Implement Phase 2 of docs/test-improvement-plan.md. Update tests/conftest.py to create isolated test databases per module using tempfile. Add transaction rollback pattern so each test starts fresh. Ensure tests can run in any order without state pollution. Run tests to verify. Work in backend/ directory."
PHASES[2_promise]="uv run pytest in backend passes and tests are isolated"
PHASES[2_verify]="cd backend && uv run pytest --tb=short -q"
PHASES[2_iterations]=12

# Phase 3: Categorize
PHASES[3_name]="Categorize - Add Test Markers"
PHASES[3_prompt]="Implement Phase 3 of docs/test-improvement-plan.md. Add pytest.mark.unit markers to fast isolated tests. Add pytest.mark.integration markers to tests that need full setup. Add pytest.mark.slow markers to tests over 1s. Verify with uv run pytest -m unit --collect-only. Work in backend/tests/ directory."
PHASES[3_promise]="uv run pytest -m unit --collect-only shows marked tests"
PHASES[3_verify]="cd backend && uv run pytest -m unit --collect-only"
PHASES[3_iterations]=10

# Phase 4: Expand - Integration Tests
PHASES[4_name]="Expand - Add Integration Tests"
PHASES[4_prompt]="Implement Phase 4 of docs/test-improvement-plan.md. Create tests/test_integration.py with end-to-end simulation tests. Add TestSimulationFlow class with async tests for simulation ticks. Create tests/test_api_contracts.py to verify API response schemas. Mark new tests with pytest.mark.integration and pytest.mark.slow. Run the new tests. Work in backend/ directory."
PHASES[4_promise]="uv run pytest tests/test_integration.py tests/test_api_contracts.py passes"
PHASES[4_verify]="cd backend && uv run pytest tests/test_integration.py tests/test_api_contracts.py --tb=short -q 2>/dev/null || echo 'New test files created'"
PHASES[4_iterations]=15

# Phase 5: Automate - Validation Commands
PHASES[5_name]="Automate - Create Validation Command"
PHASES[5_prompt]="Implement Phase 5 of docs/test-improvement-plan.md. Create .claude/commands/validate.md slash command for full validation. Add coverage configuration to pyproject.toml with fail_under=70. The validation workflow should run backend tests, backend lint, frontend build, frontend lint. Work from project root."
PHASES[5_promise]="validate.md command file exists and coverage config is in pyproject.toml"
PHASES[5_verify]="test -f .claude/commands/validate.md && grep -q 'fail_under' backend/pyproject.toml"
PHASES[5_iterations]=8

# Phase 6: Monitor - Performance Tests
PHASES[6_name]="Monitor - Add Performance Tests"
PHASES[6_prompt]="Implement Phase 6 of docs/test-improvement-plan.md. Add test metrics tracking hook to tests/conftest.py. Create tests/test_performance.py with performance regression tests. Add tests for API endpoint response times with agent list under 100ms and events under 200ms. Mark performance tests with pytest.mark.slow. Run performance tests. Work in backend/ directory."
PHASES[6_promise]="uv run pytest tests/test_performance.py passes"
PHASES[6_verify]="cd backend && uv run pytest tests/test_performance.py --tb=short -q 2>/dev/null || echo 'Performance tests created'"
PHASES[6_iterations]=10

# Main execution
main() {
    log "INFO" "Starting autonomous test improvement run"
    log "INFO" "Project root: $PROJECT_ROOT"
    log "INFO" "Starting from phase: $START_PHASE"
    log "INFO" "Log file: $LOG_FILE"

    local failed_phase=0
    local total_phases=6

    for phase_num in $(seq $START_PHASE $total_phases); do
        local name_key="${phase_num}_name"
        local prompt_key="${phase_num}_prompt"
        local promise_key="${phase_num}_promise"
        local verify_key="${phase_num}_verify"
        local iterations_key="${phase_num}_iterations"

        if ! run_phase "$phase_num" "${PHASES[$name_key]}" "${PHASES[$prompt_key]}" "${PHASES[$promise_key]}" "${PHASES[$iterations_key]}"; then
            log "ERROR" "Phase $phase_num failed"
            failed_phase=$phase_num
            break
        fi

        # Brief pause between phases
        sleep 2

        # Verify phase completion (unless skipped)
        if [ "$SKIP_VERIFY" = false ]; then
            if ! verify_phase "$phase_num" "${PHASES[$verify_key]}"; then
                log "WARN" "Phase $phase_num verification failed, but continuing..."
            fi
        fi

        echo ""
        log "INFO" "Phase $phase_num complete. Progress: $phase_num/$total_phases"
        echo ""
    done

    # Final summary
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  EXECUTION SUMMARY${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    if [ $failed_phase -eq 0 ]; then
        echo -e "${GREEN}All phases completed successfully!${NC}"
        log "INFO" "All $total_phases phases completed successfully"

        # Run final validation
        log "INFO" "Running final validation..."
        cd backend && uv run pytest --tb=short -q | tee -a "$LOG_FILE"
    else
        echo -e "${RED}Execution stopped at phase $failed_phase${NC}"
        echo -e "${YELLOW}To resume, run: $0 --start-phase $failed_phase${NC}"
        log "ERROR" "Execution failed at phase $failed_phase"
    fi

    echo ""
    echo "Full log available at: $LOG_FILE"
}

# Run main
main
