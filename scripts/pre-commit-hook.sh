#!/bin/bash
#
# Pre-commit hook for Clockwork Hamlet
# Phase 5.1: Run fast tests before allowing commits
#
# Installation:
#   ln -sf ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
#   # Or for worktrees, create in main repo:
#   cp scripts/pre-commit-hook.sh /path/to/main/repo/.git/hooks/pre-commit
#
# This hook ensures code quality by running:
# 1. Backend unit tests (fast, isolated)
# 2. Backend linting with ruff
#
# To skip this hook (use sparingly):
#   git commit --no-verify
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pre-commit checks...${NC}"

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if backend directory exists
if [ ! -d "$REPO_ROOT/backend" ]; then
    echo -e "${YELLOW}No backend directory found, skipping backend tests${NC}"
    exit 0
fi

# Run backend unit tests
echo -e "\n${YELLOW}[1/2] Running backend unit tests...${NC}"
cd "$REPO_ROOT/backend"
if uv run pytest -m unit --tb=short -q 2>/dev/null; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed. Commit aborted.${NC}"
    echo -e "${YELLOW}Run 'cd backend && uv run pytest -m unit -v' for details${NC}"
    exit 1
fi

# Run backend linting
echo -e "\n${YELLOW}[2/2] Running backend linting...${NC}"
if uv run ruff check . --quiet 2>/dev/null; then
    echo -e "${GREEN}✓ Linting passed${NC}"
else
    echo -e "${RED}✗ Linting failed. Commit aborted.${NC}"
    echo -e "${YELLOW}Run 'cd backend && uv run ruff check .' for details${NC}"
    exit 1
fi

echo -e "\n${GREEN}All pre-commit checks passed!${NC}"
exit 0
