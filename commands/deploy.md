---
name: phantom:deploy
description: Build, deploy, and verify the configured deployment target
arguments:
  - name: target
    description: Deployment target name (from config)
    required: false
  - name: skip-tests
    description: Skip pre-deployment tests
    required: false
  - name: skip-security
    description: Skip pre-deployment security check
    required: false
---

# /phantom:deploy

Build, deploy, and verify the configured deployment target.

## Usage

```
/phantom:deploy
/phantom:deploy --target production
/phantom:deploy --skip-tests
```

## What It Does

Runs the full deployment pipeline:

```
BUILD → TEST → SECURITY CHECK → DEPLOY → HEALTH CHECK → VERIFY
```

## Supported Targets

- **Vercel** - `vercel` adapter
- **Netlify** - `netlify` adapter
- **Cloudflare Pages** - `cloudflare_pages` adapter
- **Docker** - `docker` adapter
- **Custom** - `custom` adapter with user-defined commands

## Configuration

Deployment configs stored in `.phantom/deploy/<name>.json`

## Pipeline Steps

1. **Build** - Runs build command for target
2. **Test** - Runs test suite (unless --skip-tests)
3. **Security Check** - Runs security audit (unless --skip-security)
4. **Deploy** - Deploys to target platform
5. **Health Check** - Verifies deployment is healthy
6. **Verify** - Confirms deployment success

## Rollback

Automatic rollback on health check failure if configured.

## Output

- `.phantom/deployment-log.md` - Deployment log
- Deployment URL
- Health check status