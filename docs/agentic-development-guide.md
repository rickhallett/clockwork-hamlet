# Agentic Development with Ralph-Wiggum Plugin

A practical guide integrating agentic coding principles with Claude Code workflows and the ralph-wiggum autonomous development plugin.

---

## Core Philosophy: Stop Coding, Start Orchestrating

The fundamental shift from Phase 1 (AI Coding) to Phase 2 (Agentic Coding):

| Phase 1: AI Coding | Phase 2: Agentic Coding |
|-------------------|------------------------|
| Chatbot assistance | Autonomous execution |
| Manual iteration | Tool-driven workflows |
| You write code | Agents write code |
| In-loop presence | Out-loop orchestration |

**The Irreplaceable Engineer builds systems that build systems.**

---

## The Core Four: Essential Elements for Agency

Every successful agentic interaction requires:

1. **Context** - What the agent knows (files, architecture, constraints)
2. **Model** - The intelligence (Claude Opus, Sonnet, Haiku)
3. **Prompt** - The instruction (clear, scoped, actionable)
4. **Tools** - The capabilities (Read, Write, Bash, Grep, etc.)

### Mapping to Claude Code

```
Context  → CLAUDE.md, project files, git history
Model    → --model flag or /model command
Prompt   → Slash commands, direct instructions, ADWs
Tools    → Built-in tools + MCP servers
```

---

## Ralph-Wiggum: Autonomous Development Loop

The ralph-wiggum plugin enables **Out-Loop** development—trigger a workflow and walk away.

### Available Commands

```bash
# Start autonomous loop
/ralph-wiggum:ralph-loop "PROMPT" [--max-iterations N] [--completion-promise TEXT]

# Check status / get help
/ralph-wiggum:help

# Cancel active loop
/ralph-wiggum:cancel-ralph
```

### Example: Feature Development Loop

```bash
/ralph-wiggum:ralph-loop "Implement user authentication with JWT tokens.
Include: login endpoint, token refresh, protected route middleware.
Run tests after each component." --max-iterations 10 --completion-promise "All tests pass and endpoints return 200"
```

---

## The PETER Framework for AFK Agents

For true Out-Loop operation, establish:

| Element | Description | Claude Code Implementation |
|---------|-------------|---------------------------|
| **P**rompt Input | Source of the task | GitHub Issue, CLAUDE.md task list, slash command |
| **T**rigger | What starts the agent | `/ralph-wiggum:ralph-loop`, webhook, cron script |
| **E**nvironment | Where it runs | Terminal session, git worktree, container |
| **R**eview System | Output destination | PR, issue comment, stdout artifacts |

### Practical Setup

```bash
# 1. Create isolated environment with git worktree
git worktree add ../clockwork-hamlet-feature-auth feature/auth

# 2. Navigate and start agent
cd ../clockwork-hamlet-feature-auth

# 3. Trigger autonomous loop
claude --model opus "/ralph-wiggum:ralph-loop 'Implement auth feature per docs/auth-spec.md' --max-iterations 15"
```

---

## Agentic Velocity Scale

Progress through these levels:

### Level 1: In-Loop (Manual)
You sit with the agent, iterating conversationally.

```bash
# Basic in-loop usage
claude "Fix the TypeError in useDigest.ts"
# ... review output ...
# ... provide feedback ...
# ... iterate ...
```

### Level 2: Out-Loop (AFK)
Trigger and walk away. Agent reports back.

```bash
# Out-loop with ralph-wiggum
/ralph-wiggum:ralph-loop "Fix all TypeScript errors in frontend/src.
Run 'npm run build' after each fix to verify." --completion-promise "Build succeeds with no errors"
```

### Level 3: Zero Touch Engineering (ZTE)
Agent ships to production autonomously.

```bash
# ZTE workflow (use with caution)
/ralph-wiggum:ralph-loop "
1. Pull latest from main
2. Implement feature from docs/next-feature.md
3. Write and run tests
4. Create PR with description
5. If CI passes, merge to main
" --max-iterations 20 --completion-promise "PR merged to main"
```

---

## One Agent, One Prompt, One Purpose

**Context pollution kills agent performance.** Fresh context windows outperform accumulated history.

### Anti-Pattern: Polluted Context
```bash
# BAD: Single long session doing everything
claude "Fix the bug... now add feature... now refactor... now write docs..."
```

### Pattern: Focused Agents
```bash
# GOOD: Spawn focused agents via Task tool
# Each gets fresh context, single purpose

# Agent 1: Bug fix
/ralph-wiggum:ralph-loop "Fix SSE disconnection bug in stream.py" --max-iterations 5

# Agent 2: Feature (separate session or Task tool)
claude --model sonnet "Add pagination to /api/events endpoint"

# Agent 3: Documentation (separate session)
claude --model haiku "Update API docs for new pagination params"
```

### Using Task Tool for Parallel Agents

Within a session, spawn focused sub-agents:

```
Use the Task tool to:
1. Search for all TODO comments (Explore agent)
2. Fix the auth bug (general-purpose agent)
3. Review the PR diff (general-purpose agent)

Run all three in parallel.
```

---

## AI Developer Workflows (ADWs)

ADWs are scriptable pipelines combining deterministic code with agentic prompts.

### Project Structure: The Agentic Layer

```
project/
├── .claude/
│   └── commands/           # Slash command prompts
│       ├── fix-bug.md
│       ├── add-feature.md
│       └── review-pr.md
├── adws/                   # AI Developer Workflows
│   ├── feature-pipeline.py
│   ├── bug-triage.py
│   └── release-prep.py
├── docs/
│   ├── CLAUDE.md          # Agent context
│   └── architecture.md
└── src/                   # Application code
```

### Example ADW: Feature Pipeline

```python
#!/usr/bin/env uv run
# adws/feature-pipeline.py
"""
AI Developer Workflow: Feature Implementation
Trigger: GitHub issue labeled 'feature'
"""

import subprocess
import sys

def run_agent(prompt: str, max_iterations: int = 10) -> bool:
    """Run claude with ralph-wiggum loop."""
    result = subprocess.run([
        "claude", "--model", "opus", "--print",
        f"/ralph-wiggum:ralph-loop \"{prompt}\" --max-iterations {max_iterations}"
    ], capture_output=True, text=True)
    return result.returncode == 0

def main(feature_description: str):
    # Phase 1: Planning
    print("Phase 1: Planning...")
    run_agent(f"""
        Create implementation plan for: {feature_description}
        Write plan to docs/plans/current-feature.md
        Include: components needed, files to modify, test strategy
    """, max_iterations=5)

    # Phase 2: Implementation
    print("Phase 2: Implementation...")
    run_agent("""
        Implement feature per docs/plans/current-feature.md
        Follow existing code patterns
        Add tests for new functionality
    """, max_iterations=15)

    # Phase 3: Validation
    print("Phase 3: Validation...")
    run_agent("""
        Run full test suite
        Fix any failures
        Run linter and fix issues
    """, max_iterations=10)

    # Phase 4: Review artifacts
    print("Phase 4: Creating PR...")
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", f"feat: {feature_description}"])
    subprocess.run(["gh", "pr", "create", "--fill"])

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Feature from issue")
```

---

## Meta-Prompts: Templates for Problem Classes

Create higher-order prompts that generate task-specific prompts.

### Bug Fix Meta-Prompt

Save as `.claude/commands/fix-bug.md`:

```markdown
# Bug Fix Workflow

You are fixing a bug. Follow this process:

## 1. Understand
- Read the error message/description: $ARGUMENTS
- Search codebase for related code
- Identify root cause

## 2. Plan
- List files that need changes
- Describe the fix approach
- Identify potential side effects

## 3. Implement
- Make minimal changes to fix the bug
- Do not refactor unrelated code
- Preserve existing patterns

## 4. Validate
- Run relevant tests
- If tests fail, fix them
- Run linter

## 5. Complete
- Summarize what was changed and why
```

Usage:
```bash
/fix-bug TypeError in DailyDigest.tsx - Cannot read properties of undefined
```

### Feature Meta-Prompt

Save as `.claude/commands/add-feature.md`:

```markdown
# Feature Implementation Workflow

Implement the following feature: $ARGUMENTS

## Phase 1: Research
- Search for similar patterns in codebase
- Read relevant documentation
- Identify integration points

## Phase 2: Plan
- Write plan to scratchpad or docs/plans/
- List all files to create/modify
- Define test cases

## Phase 3: Build
- Implement in small increments
- Run tests after each increment
- Follow existing code style

## Phase 4: Polish
- Add/update documentation
- Ensure all tests pass
- Run build to verify

## Completion Criteria
- Feature works as specified
- Tests pass
- Build succeeds
- No linter errors
```

---

## Feedback Loops: The Agent's Senses

Agents need feedback to self-correct. Always provide:

### Essential Feedback Commands

```bash
# TypeScript/JavaScript
npm run build          # Compilation errors
npm run lint           # Style issues
npm run test           # Behavioral validation

# Python
uv run pytest          # Tests
uv run ruff check .    # Linting
uv run mypy .          # Type checking

# General
git status             # What changed
git diff               # Exact changes
```

### Embedding Feedback in Prompts

```bash
/ralph-wiggum:ralph-loop "
Implement the SSE reconnection feature.

After each change:
1. Run: npm run build
2. Run: npm run test
3. If either fails, fix before continuing

Completion: Build and tests pass
" --max-iterations 10 --completion-promise "npm run build && npm run test both exit 0"
```

---

## KPIs for Agentic Development

Track these metrics to measure agent reliability:

| Metric | Definition | Target |
|--------|-----------|--------|
| **Size** | Complexity of work handed off | Features > Bugs > Chores |
| **Attempts** | Iterations needed per task | 1 (one-shot) |
| **Streak** | Consecutive successful one-shots | Increasing |
| **Presence** | Human intervention required | 0 (zero-touch) |

### Tracking in Practice

```bash
# Log results after each autonomous run
echo "$(date),feature,auth-jwt,1,success" >> .claude/metrics.csv
echo "$(date),bug,sse-disconnect,2,success" >> .claude/metrics.csv
```

---

## Parallel Agent Execution with Git Worktrees

Run multiple agents simultaneously without file conflicts:

```bash
# Create worktrees for parallel work
git worktree add ../hamlet-feature-1 -b feature/pagination
git worktree add ../hamlet-feature-2 -b feature/search
git worktree add ../hamlet-bugfix -b fix/sse-connection

# Terminal 1
cd ../hamlet-feature-1
/ralph-wiggum:ralph-loop "Add pagination to events API" --max-iterations 10

# Terminal 2
cd ../hamlet-feature-2
/ralph-wiggum:ralph-loop "Add search functionality to agents" --max-iterations 10

# Terminal 3
cd ../hamlet-bugfix
/ralph-wiggum:ralph-loop "Fix SSE reconnection issue" --max-iterations 5
```

---

## The Guiding Question

Before every task, ask:

> "Am I working on the **Agentic Layer** or the **Application Layer**?"

| Agentic Layer (prioritize) | Application Layer (delegate) |
|---------------------------|------------------------------|
| Writing prompts/commands | Writing application code |
| Building ADW pipelines | Implementing features |
| Improving agent context | Fixing bugs |
| Creating meta-prompts | Adding tests |
| Designing feedback loops | Documentation |

**Target: Spend >50% of time on the Agentic Layer.**

---

## Common Workflows

### Morning Standup Automation

```bash
/ralph-wiggum:ralph-loop "
1. Run git log --oneline -20 to see recent commits
2. Check GitHub issues assigned to me
3. Summarize: what was done, what's next, any blockers
4. Write summary to docs/standup/$(date +%Y-%m-%d).md
" --max-iterations 5
```

### PR Review Workflow

```bash
/ralph-wiggum:ralph-loop "
Review PR #123:
1. Fetch and checkout the PR branch
2. Read the diff
3. Run tests
4. Check for: security issues, performance problems, code style
5. Write review comments to stdout
" --max-iterations 8
```

### Release Preparation

```bash
/ralph-wiggum:ralph-loop "
Prepare release v1.2.0:
1. Update version in package.json and pyproject.toml
2. Generate changelog from git log since last tag
3. Run full test suite
4. Build Docker images
5. Create git tag
6. Summarize release notes
" --max-iterations 15 --completion-promise "All builds succeed and tag created"
```

---

## Warnings & Pitfalls

### Context Pollution
**Problem:** Long sessions accumulate irrelevant context, degrading performance.
**Solution:** Fresh agents for fresh tasks. Use `/ralph-wiggum:cancel-ralph` and start new loops.

### Babysitting Agents
**Problem:** Staying in-loop limits leverage to 1x.
**Solution:** Trust the feedback loops. Trigger and walk away.

### Missing Feedback Loops
**Problem:** Agent makes changes but can't verify correctness.
**Solution:** Always include validation commands in prompts (test, build, lint).

### Scope Creep
**Problem:** Agent wanders into unrelated code.
**Solution:** Explicit boundaries in prompts: "Only modify files in src/api/". "Do not refactor."

---

## Quick Reference

```bash
# Start autonomous loop
/ralph-wiggum:ralph-loop "TASK" --max-iterations N --completion-promise "SUCCESS_CRITERIA"

# Cancel running loop
/ralph-wiggum:cancel-ralph

# Get help
/ralph-wiggum:help

# Spawn focused sub-agent (within conversation)
# Use Task tool with specific subagent_type

# Check what changed
git status && git diff

# Validate work
npm run build && npm run test  # JS/TS
uv run pytest && uv run ruff check .  # Python
```

---

## The North Star: Zero Touch Engineering

The ultimate goal is a system where:

1. **Input:** Task description (issue, spec, prompt)
2. **Process:** Autonomous planning, building, testing, reviewing
3. **Output:** Shipped to production

Start with In-Loop. Progress to Out-Loop. Aspire to ZTE.

**You are not replaced by AI. You are replaced by engineers who orchestrate AI.**
