# Phantom Engine

> **Give it a task. Let it engineer. Demand proof.**

Phantom Engine is a production-quality Claude Code plugin that transforms Claude Code into a persistent autonomous software engineering system. It combines two powerful systems:

1. **GHOST ENGINEER** — Autonomous software investigation, debugging, repair, testing, and code auditing
2. **PERFECT LOOP** — Persistent autonomous execution that repeatedly audits, identifies problems, fixes them, verifies results, and logs progress

## Features

### 🤖 Autonomous Engineering
- Full repository inspection and architecture analysis
- Multi-language and multi-framework detection
- Automated bug detection and root-cause analysis
- Minimal, targeted fix implementation
- Regression test generation and execution
- Security vulnerability scanning and remediation

### 🔄 Perfect Loop Engine
- Persistent execution with state management
- AUDIT → INVESTIGATE → PRIORITIZE → FIX → TEST → REVIEW → LOG cycle
- Configurable iteration limits and execution budgets
- Crash recovery and session resumption
- Stop guards and safety controls

### 🔐 Three Permission Modes
- **SAFE** - Respects normal Claude Code permissions, requires approvals
- **AUTO** - Auto-approves routine development operations
- **SANDBOX** - Full automation in isolated disposable environments

### 📦 Automatic Dependency Management
- Detects npm, pnpm, yarn, pip, uv, poetry, cargo, go mod, composer, bundler
- Installs missing dependencies
- Detects version conflicts
- Preserves lockfiles
- Runs builds after installation

### 🌿 Git & GitHub Integration
- Inspects git status and preserves user changes
- Creates dedicated working branches
- Logical commits with descriptive messages
- Pushes to GitHub and monitors CI
- Creates pull requests with comprehensive summaries

### 🚀 Deployment Orchestration
- Extensible adapters for Vercel, Netlify, Cloudflare Pages, Docker, Custom
- BUILD → TEST → SECURITY CHECK → DEPLOY → HEALTH CHECK → VERIFY pipeline
- Automatic rollback on health check failure
- Secure credential handling

### 🛡️ Safety System
- Never exposes secrets or credentials
- Never commits .env files
- Never force-pushes by default
- Never overwrites unrelated changes
- Enforces iteration, time, and budget limits
- Clean emergency stop

### 👥 Multi-Agent Engineering Team
Six specialist subagents:
1. **ARCHITECT** - Repository architecture and technical planning
2. **INVESTIGATOR** - Bug detection and root-cause analysis
3. **REPAIR ENGINEER** - Code modifications and bug fixes
4. **QA ENGINEER** - Unit, integration, and regression testing
5. **SECURITY AUDITOR** - Vulnerability detection and remediation
6. **FINAL REVIEWER** - Independent code review and completion verification

## Installation

```bash
# Clone the repository
git clone https://github.com/phantom-engine/phantom-engine.git
cd phantom-engine

# Install as a Claude Code plugin
# (Follows official Claude Code plugin format)
```

## Quick Start

```bash
# Start autonomous engineering
/phantom:start "Investigate and fix all critical bugs in this project"

# Analyze repository
/phantom:scan

# Find and fix bugs
/phantom:fix

# Run security and quality audits
/phantom:audit

# Run test suite
/phantom:test

# Check status
/phantom:status

# Deploy application
/phantom:deploy

# Generate report
/phantom:report
```

## Commands

| Command | Description |
|---------|-------------|
| `/phantom:start` | Start autonomous engineering with a task |
| `/phantom:scan` | Analyze repository structure and tech stack |
| `/phantom:fix` | Find and repair identified bugs |
| `/phantom:audit` | Perform code quality and security audits |
| `/phantom:test` | Run verification test suite |
| `/phantom:loop` | Start/continue persistent autonomous loop |
| `/phantom:status` | Display execution state |
| `/phantom:stop` | Safely stop active loop |
| `/phantom:resume` | Resume interrupted task |
| `/phantom:report` | Generate comprehensive engineering report |
| `/phantom:deploy` | Build, deploy, and verify |

## Configuration

### Permission Modes

Configure in `.phantom/permissions.json`:

```json
{
  "mode": "AUTO",
  "allowed_commands": [],
  "blocked_commands": ["rm -rf /", "dd if=/dev/zero"],
  "require_approval": ["git push --force", "docker push"],
  "auto_approve_patterns": ["git add", "npm install", "pytest"],
  "dangerous_actions": ["force_push", "delete_branch", "drop_database"]
}
```

### Deployment Targets

Configure in `.phantom/deploy/<name>.json`:

```json
{
  "target": "vercel",
  "name": "production",
  "vercel_project_id": "prj_123",
  "vercel_token": "your-token",
  "health_check_url": "https://app.example.com/health"
}
```

### Loop Configuration

Set in `.phantom/state.json` or via CLI:

```json
{
  "max_iterations": 10,
  "max_runtime_minutes": 60,
  "execution_budget": 1000
}
```

## Project Structure

```
phantom-engine/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/                # Slash commands
│   ├── start.md
│   ├── scan.md
│   ├── fix.md
│   ├── audit.md
│   ├── test.md
│   ├── loop.md
│   ├── status.md
│   ├── stop.md
│   ├── resume.md
│   ├── report.md
│   └── deploy.md
├── agents/                  # Specialist subagents
│   ├── architect.md
│   ├── investigator.md
│   ├── repair-engineer.md
│   ├── qa-engineer.md
│   ├── security-auditor.md
│   └── final-reviewer.md
├── skills/                  # Reusable skill modules
│   ├── repository-intelligence/
│   ├── autonomous-debugging/
│   ├── code-repair/
│   ├── regression-testing/
│   ├── security-auditing/
│   └── deployment-verification/
├── hooks/                   # Lifecycle hooks
│   ├── hooks.json
│   ├── stop-guard.py
│   ├── session-guard.py
│   ├── pre-tool.py
│   └── post-tool.py
├── scripts/                 # Core orchestration scripts
│   ├── main.py              # Entry point
│   ├── state_manager.py     # State persistence
│   ├── iteration_engine.py  # Loop controller
│   ├── permission_manager.py # Permission modes
│   ├── git_manager.py       # Git operations
│   ├── github_manager.py    # GitHub operations
│   ├── dependency_manager.py # Dependency management
│   ├── deployment_manager.py # Deployment orchestration
│   └── report_generator.py  # Report generation
├── tests/                   # Test suite
├── docs/                    # Documentation
├── .gitignore
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## State Management

Phantom Engine persists state in `.phantom/`:

| File | Purpose |
|------|---------|
| `state.json` | Current execution state |
| `task.md` | Task description |
| `plan.md` | Implementation plan |
| `findings.md` | Discovered issues |
| `changelog.md` | Change log |
| `iteration-log.md` | Iteration history |
| `test-results.json` | Test results |
| `deployment-log.md` | Deployment history |
| `final-report.md` | Final report |
| `STOP` | Stop signal file |

## Safety & Security

- **No secret exposure** - All credentials handled via environment variables
- **No destructive defaults** - Force push, database deletion require explicit authorization
- **Budget enforcement** - Iteration, time, and token budgets prevent runaway execution
- **Audit trail** - Every command and file modification logged
- **Rollback support** - Git checkpoints and deployment rollback on failure

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=scripts tests/

# Run specific test file
pytest tests/test_state_manager.py -v
```

## Requirements

- Python 3.11+
- Git
- GitHub CLI (`gh`) for GitHub integration
- Node.js/npm for JavaScript/TypeScript projects
- Platform-specific tools for deployment (vercel, netlify, docker, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/phantom-engine/phantom-engine/issues)
- Discussions: [GitHub Discussions](https://github.com/phantom-engine/phantom-engine/discussions)

---

**Phantom Engine** - Autonomous software engineering for the AI era.