---
name: phantom:start
description: Start autonomous engineering with Phantom Engine
arguments:
  - name: task
    description: The engineering task to perform
    required: true
  - name: mode
    description: Permission mode (SAFE, AUTO, SANDBOX)
    required: false
  - name: max-iterations
    description: Maximum iterations to run
    required: false
  - name: budget
    description: Execution budget
    required: false
---

# /phantom:start

Start the Phantom Engine autonomous engineering loop.

## Usage

```
/phantom:start "Investigate and fix all critical bugs in this project"
/phantom:start "Add user authentication with JWT tokens" --mode AUTO --max-iterations 15
/phantom:start "Optimize database queries and add caching" --mode SANDBOX --budget 2000
```

## What Happens

1. **Initialize** - Creates `.phantom/` directory and state
2. **Scan** - Analyzes repository architecture, languages, dependencies
3. **Plan** - Creates implementation plan in `plan.md`
4. **Execute** - Runs AUDIT → INVESTIGATE → PRIORITIZE → FIX → TEST → REVIEW → LOG cycle
5. **Verify** - Runs tests, security checks, build verification
6. **Deploy** - Optional deployment if configured
7. **Report** - Generates comprehensive final report

## Permission Modes

- **SAFE** - Requires approval for all modifications (default for new users)
- **AUTO** - Auto-approves routine development operations
- **SANDBOX** - Full auto in isolated environment (requires explicit setup)

## State Persistence

State is saved to `.phantom/state.json` and can be resumed with `/phantom:resume`.

## Stopping

Create `.phantom/STOP` file or use `/phantom:stop` to gracefully halt.