---
name: deployment-verification
description: Deployment orchestration, health checking, and rollback management
---

# Deployment Verification Skill

Provides deployment orchestration and verification capabilities for Phantom Engine.

## Capabilities

1. **Deployment Pipeline**
   - Build verification
   - Test execution gate
   - Security check gate
   - Multi-environment deployment
   - Blue-green / canary deployments

2. **Platform Adapters**
   - Vercel
   - Netlify
   - Cloudflare Pages
   - AWS (ECS, Lambda, Elastic Beanstalk)
   - GCP (Cloud Run, App Engine)
   - Azure (Container Apps, Static Web Apps)
   - Kubernetes (Helm, Kustomize)
   - Docker (Compose, Swarm)
   - Custom commands

3. **Health Checking**
   - HTTP endpoint verification
   - Database connectivity
   - Cache connectivity
   - External service dependencies
   - Custom health check scripts
   - Timeout and retry configuration

4. **Rollback Management**
   - Automatic rollback on health failure
   - Manual rollback trigger
   - Rollback verification
   - Previous version tracking

5. **Deployment Verification**
   - Smoke tests post-deployment
   - Performance baseline comparison
   - Error rate monitoring
   - Feature flag verification

## Pipeline Stages

```
BUILD → TEST → SECURITY CHECK → DEPLOY → HEALTH CHECK → VERIFY → COMPLETE
                ↓                    ↓
             FAIL                FAIL
                ↓                    ↓
            STOP               ROLLBACK
```

## Configuration

Deployment targets configured in `.phantom/deploy/<name>.json`

## Output

- `.phantom/deployment-log.md` - Deployment log
- Deployment URL and status
- Health check results
- Rollback status if applicable