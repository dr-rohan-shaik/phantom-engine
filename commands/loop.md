---
name: phantom:loop
description: Start or continue the persistent autonomous loop
arguments:
  - name: continue
    description: Continue from previous state
    required: false
---

# /phantom:loop

Start or continue the Phantom Engine persistent autonomous loop.

## Usage

```
/phantom:loop
/phantom:loop --continue
```

## What It Does

The loop runs the continuous engineering cycle:

```
AUDIT → INVESTIGATE → PRIORITIZE → FIX → TEST → REVIEW → LOG → REPEAT
```

Each iteration:
1. Audits the codebase for issues
2. Investigates root causes
3. Prioritizes fixes by impact
4. Implements fixes
5. Runs tests to verify
6. Reviews changes
7. Logs results

## Loop Controls

- **Max Iterations** - Configured in state (default 10)
- **Execution Budget** - Token/action budget (default 1000)
- **Runtime Limit** - Maximum runtime in minutes (default 60)
- **Stop Conditions** - Verification complete, STOP file, explicit stop request

## State Persistence

Loop state is saved to `.phantom/state.json` after each iteration.
Can be resumed with `/phantom:resume` or `/phantom:loop --continue`.

## Stopping

- Create `.phantom/STOP` file
- Use `/phantom:stop`
- Press Ctrl+C (will trigger stop guard)