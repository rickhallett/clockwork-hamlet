#!/bin/bash
#
# setup-worktree.sh - Create a git worktree for parallel agent development
#
# Usage: ./scripts/setup-worktree.sh <worktree-name> <branch-name> [base-branch]
#
# Example:
#   ./scripts/setup-worktree.sh track-a-feed feat/feed/export-csv master
#
# This script:
#   1. Creates a git worktree in the parent worktrees directory
#   2. Copies .env* files and essential dot-folders
#   3. Installs dependencies (backend + frontend)
#   4. Initializes the coordination database entry
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <worktree-name> <branch-name> [base-branch]"
    echo ""
    echo "Arguments:"
    echo "  worktree-name  Name for the worktree directory (e.g., track-a-feed)"
    echo "  branch-name    Git branch to create/checkout (e.g., feat/feed/export)"
    echo "  base-branch    Base branch to create from (default: master)"
    exit 1
fi

WORKTREE_NAME="$1"
BRANCH_NAME="$2"
BASE_BRANCH="${3:-master}"

# Detect paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_NAME="$(basename "$REPO_ROOT")"

# Check if we're in a worktree (not the main repo)
if git rev-parse --is-inside-work-tree &>/dev/null; then
    GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null)"
    GIT_DIR="$(git rev-parse --git-dir 2>/dev/null)"

    # If git-common-dir differs from git-dir, we're in a worktree
    if [ "$GIT_COMMON_DIR" != "$GIT_DIR" ] && [ "$GIT_COMMON_DIR" != ".git" ]; then
        log_error "This script must be run from the MAIN repository, not a worktree!"
        log_error "Main repo is at: $(dirname "$GIT_COMMON_DIR")"
        exit 1
    fi
fi

# Fixed coordination directory - shared by ALL worktrees
# Uses ~/.claude-coordination/<repo-name>/ to ensure single DB regardless of where script runs
COORDINATION_DIR="$HOME/.claude-coordination/$REPO_NAME"
COORDINATION_DB="$COORDINATION_DIR/agents.db"

# Worktrees go in a sibling directory to the main repo
WORKTREES_ROOT="$(dirname "$REPO_ROOT")/worktrees-$REPO_NAME"
WORKTREE_PATH="$WORKTREES_ROOT/$WORKTREE_NAME"

log_info "Repository root: $REPO_ROOT"
log_info "Worktrees root: $WORKTREES_ROOT"
log_info "Creating worktree: $WORKTREE_PATH"
log_info "Branch: $BRANCH_NAME (from $BASE_BRANCH)"

# Create worktrees directory structure
mkdir -p "$WORKTREES_ROOT"
mkdir -p "$COORDINATION_DIR"
mkdir -p "$COORDINATION_DIR/logs"

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
    log_error "Worktree already exists: $WORKTREE_PATH"
    exit 1
fi

# Create the git worktree
log_info "Creating git worktree..."
cd "$REPO_ROOT"

# Check if branch exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    log_info "Branch exists, checking out..."
    git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
else
    log_info "Creating new branch from $BASE_BRANCH..."
    git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "$BASE_BRANCH"
fi

# Copy .env* files
log_info "Copying environment files..."
for envfile in "$REPO_ROOT"/.env*; do
    if [ -f "$envfile" ]; then
        filename=$(basename "$envfile")
        cp "$envfile" "$WORKTREE_PATH/$filename"
        log_info "  Copied $filename"
    fi
done

# Copy essential dot-folders (excluding .git which is handled by worktree)
log_info "Copying dot-folders..."
DOT_FOLDERS=(".claude" ".vscode" ".idea")
for folder in "${DOT_FOLDERS[@]}"; do
    if [ -d "$REPO_ROOT/$folder" ]; then
        cp -r "$REPO_ROOT/$folder" "$WORKTREE_PATH/"
        log_info "  Copied $folder/"
    fi
done

# Copy backend .env if it exists
if [ -f "$REPO_ROOT/backend/.env" ]; then
    cp "$REPO_ROOT/backend/.env" "$WORKTREE_PATH/backend/.env"
    log_info "  Copied backend/.env"
fi

# Copy frontend .env* files
for envfile in "$REPO_ROOT"/frontend/.env*; do
    if [ -f "$envfile" ]; then
        filename=$(basename "$envfile")
        cp "$envfile" "$WORKTREE_PATH/frontend/$filename"
        log_info "  Copied frontend/$filename"
    fi
done

# Install backend dependencies
log_info "Installing backend dependencies..."
cd "$WORKTREE_PATH/backend"
if [ -f "pyproject.toml" ]; then
    uv sync 2>/dev/null || log_warn "uv sync failed - may need manual setup"
fi

# Install frontend dependencies (optional, can be slow)
if [ "${SKIP_FRONTEND:-}" != "1" ]; then
    log_info "Installing frontend dependencies..."
    cd "$WORKTREE_PATH/frontend"
    if [ -f "package.json" ]; then
        npm install 2>/dev/null || bun install 2>/dev/null || log_warn "Frontend install failed"
    fi
else
    log_info "Skipping frontend dependencies (SKIP_FRONTEND=1)"
fi

# Initialize coordination database if it doesn't exist
if [ ! -f "$COORDINATION_DB" ]; then
    log_info "Initializing coordination database..."
    sqlite3 "$COORDINATION_DB" <<'EOF'
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track TEXT UNIQUE NOT NULL,
    worktree_path TEXT NOT NULL,
    branch TEXT NOT NULL,
    ticket_id TEXT,
    status TEXT DEFAULT 'idle' CHECK(status IN ('idle', 'working', 'blocked', 'review', 'done')),
    current_task TEXT,
    started_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_pid INTEGER
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_track TEXT NOT NULL,
    to_track TEXT,  -- NULL means broadcast
    message_type TEXT NOT NULL CHECK(message_type IN ('info', 'warning', 'blocker', 'question', 'done')),
    content TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    locked_by TEXT NOT NULL,
    locked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_messages_to ON messages(to_track, acknowledged);
CREATE INDEX idx_file_locks_path ON file_locks(file_path);
EOF
fi

# Register this worktree in the coordination database
log_info "Registering worktree in coordination database..."
sqlite3 "$COORDINATION_DB" <<EOF
INSERT OR REPLACE INTO agents (track, worktree_path, branch, status, updated_at)
VALUES ('$WORKTREE_NAME', '$WORKTREE_PATH', '$BRANCH_NAME', 'idle', CURRENT_TIMESTAMP);
EOF

# Create a local coordination config file in the worktree
cat > "$WORKTREE_PATH/.coordination.env" <<EOF
# Auto-generated coordination config
COORDINATION_DB=$COORDINATION_DB
COORDINATION_DIR=$COORDINATION_DIR
TRACK_NAME=$WORKTREE_NAME
BRANCH_NAME=$BRANCH_NAME
EOF

log_info ""
log_info "=========================================="
log_info "Worktree created successfully!"
log_info "=========================================="
log_info ""
log_info "Location: $WORKTREE_PATH"
log_info "Branch:   $BRANCH_NAME"
log_info "Track:    $WORKTREE_NAME"
log_info ""
log_info "Coordination DB: $COORDINATION_DB"
log_info ""
log_info "To start working:"
log_info "  cd $WORKTREE_PATH"
log_info ""
log_info "To remove this worktree later:"
log_info "  git worktree remove $WORKTREE_PATH"
log_info ""
