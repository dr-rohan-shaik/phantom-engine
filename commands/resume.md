---
name: phantom:resume
description: Resume an interrupted Phantom Engine task
arguments:
  - name: task
    description: New task to override resumed task
    required: false
---

# /phantom:resume

Resume an interrupted Phantom Engine task from saved state.

## Usage

```
/phantom:resume
/phantom:resume "New task description"
```

## What It Does

1. Loads state from `.phantom/state.json`
2. Verifies previous session was incomplete
3. Continues from the last completed iteration
4. Optionally accepts a new task to override

## Requirements

- Previous `.phantom/state.json` must exist
- Previous session must not have been completed
- Stop must not have been explicitly requested

## Output

Resumes the engineering loop from where it left off.