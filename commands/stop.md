---
name: phantom:stop
description: Safely stop the active Phantom Engine loop
arguments:
  - name: force
    description: Force stop without saving state
    required: false
---

# /phantom:stop

Safely stop the active Phantom Engine loop.

## Usage

```
/phantom:stop
/phantom:stop --force
```

## What It Does

1. Creates `.phantom/STOP` file
2. Sets `stop_requested: true` in state
3. Allows current iteration to complete
4. Saves final state
5. Generates final report

## Force Stop

`--force` immediately stops without waiting for current iteration to complete.
Use only in emergencies.