# Emergency Rollback Procedures - Claude Guardian

**Created:** 2025-08-28T08:17:00+02:00
**Backup Branch:** `cleanup-backup-20250828-0813`

## 🚨 EMERGENCY ROLLBACK - IMMEDIATE ACTIONS

### Quick Rollback (30 seconds)
```bash
# Switch to backup branch immediately
git checkout cleanup-backup-20250828-0813

# Verify rollback successful
git branch --show-current
```

**Expected Output:** `cleanup-backup-20250828-0813`

### Full System Restore (2 minutes)
```bash
# 1. Switch to backup
git checkout cleanup-backup-20250828-0813

# 2. Restart all services
docker-compose down
docker-compose up -d

# 3. Verify services
docker-compose ps
```

### Create New Main Branch (Emergency)
If main branch is corrupted:
```bash
# Create new main from backup
git checkout cleanup-backup-20250828-0813
git checkout -b main-emergency-restore

# Force push new main (CAUTION)
git push origin main-emergency-restore --force-with-lease
```

## 🔧 Service Recovery Commands

### Database Services
```bash
# Restart databases only
docker-compose restart claude-guardian-postgres
docker-compose restart claude-guardian-redis
docker-compose restart claude-guardian-qdrant
```

### Health Checks
```bash
# PostgreSQL
docker-compose exec claude-guardian-postgres pg_isready -U cguser -d claude_guardian

# Redis
docker-compose exec claude-guardian-redis redis-cli ping

# Qdrant
curl -f http://localhost:6333/health
```

## 📞 Emergency Verification

After rollback, verify these components:

### ✅ Must Work
- [ ] `git branch --show-current` shows backup branch
- [ ] `docker-compose ps` shows healthy containers
- [ ] `python -c "from claude_guardian.main import app; print('OK')"` succeeds

### ⚠️ Should Work
- [ ] PostgreSQL connection test
- [ ] Redis connection test
- [ ] Qdrant HTTP endpoint accessible

## 🚦 Rollback Success Criteria

**Rollback is successful when:**
1. Git branch switched to `cleanup-backup-20250828-0813`
2. All Docker services show "healthy" status
3. FastAPI application imports without errors
4. No critical errors in service logs

## 📋 Post-Rollback Actions

1. **Document the issue** that required rollback
2. **Preserve error logs** for analysis
3. **Notify stakeholders** of rollback completion
4. **Plan recovery strategy** before attempting cleanup again

---

**BACKUP VERIFICATION:**
- Branch: `cleanup-backup-20250828-0813` ✅
- Remote: `origin/cleanup-backup-20250828-0813` ✅
- Tested: 2025-08-28T08:17:00+02:00 ✅