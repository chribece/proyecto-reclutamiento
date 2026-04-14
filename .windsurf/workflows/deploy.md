---
description: Deployment workflow for the recruitment application
tags: [deployment, production, render]
---

# Deployment Workflow

## Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Database migrations tested
- [ ] Environment variables configured in Render
- [ ] Database URL configured
- [ ] Secret key configured
- [ ] Debug mode disabled for production

## Deployment Steps

1. **Commit all changes**
   ```bash
   git add -A
   git commit -m "Prepare for deployment: [description]"
   git push origin main
   ```

2. **Monitor deployment on Render**
   - Check Render dashboard for build status
   - Monitor logs for any startup errors
   - Wait for health check to pass

3. **Verify deployment**
   - Access application URL
   - Check `/api/health` endpoint returns 200
   - Verify database connections working

## Post-Deployment Verification

- [ ] Admin login working
- [ ] Reclutador login working
- [ ] Gerente login working
- [ ] Candidato registration working
- [ ] Database tables accessible
- [ ] No error logs in Render dashboard

## Rollback Procedure

If deployment fails:
1. Check Render logs for errors
2. Revert to previous commit if needed:
   ```bash
   git revert HEAD
   git push origin main
   ```
3. Monitor rollback status

## Environment Variables Required

```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
FLASK_ENV=production
RENDER=true
```
