# Claude Guardian - Rollback Procedures

**Emergency Rollback Documentation**  
**Created**: August 27, 2025  
**Version**: Post-Harmonization v2.0.0-alpha  

---

## 🚨 Emergency Rollback Overview

### Available Rollback Points

1. **Pre-Harmonization Stable Baseline** - `commit 5f77206`
2. **Pre-Go Removal** - `commit bdb7db4`  
3. **Pre-Legacy Cleanup** - `commit f5d21cf`

---

## 🎯 Quick Rollback Commands

### Option 1: Hard Reset to Stable Baseline
```bash
cd /Users/roble/Documents/Python/claude_guardian

# Create emergency backup of current state
git branch emergency-backup-$(date +%Y%m%d-%H%M%S)

# Hard reset to pre-harmonization baseline
git reset --hard 5f77206

# Force push if needed (DANGEROUS - use only in emergency)
# git push --force-with-lease origin main
```

### Option 2: Soft Rollback (Preserves Work)
```bash
# Create revert commit (safer approach)
git revert --no-edit 126bc01..HEAD

# Or revert specific harmonization commit
git revert --no-edit 126bc01
```

---

## 🔄 Rollback Procedures by Component

### 1. Service Configuration Rollback
```bash
# Restore original docker-compose.yml
git checkout 5f77206 -- docker-compose.yml

# Restore original environment configs
git checkout 5f77206 -- config/environments/

# Restart services with old config
docker-compose down --volumes
docker-compose up -d
```

### 2. Code Naming Rollback
```bash
# Restore IFF Guardian naming
git checkout 5f77206 -- src/iff_guardian/

# Update any references
find . -name "*.py" -type f -exec sed -i '' 's/claude_guardian/iff_guardian/g' {} \;
find . -name "*.md" -type f -exec sed -i '' 's/claude_guardian/iff_guardian/g' {} \;
```

### 3. Dependencies Rollback
```bash
# Restore original requirements
git checkout 5f77206 -- requirements.txt requirements-dev.txt

# Reinstall old dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 📋 Data Recovery Procedures

### Database Rollback
```bash
# Stop services
docker-compose down

# Backup current data
cp -r ./data ./data-backup-$(date +%Y%m%d-%H%M%S)

# Remove harmonized data
rm -rf ./data/*

# Restore from backup if available
# cp -r /path/to/old/data/* ./data/

# Restart with clean state
docker-compose up -d
```

### Configuration Recovery
```bash
# Restore .env from template
cp .env.template .env.backup
git checkout 5f77206 -- .env.example
cp .env.example .env

# Manual configuration required for:
# - Database passwords
# - JWT secrets
# - External service keys
```

---

## 🛠️ Recovery Validation

### Post-Rollback Checks
```bash
# 1. Verify service startup
docker-compose ps

# 2. Check application health
curl -f http://localhost:8000/health || echo "App health check failed"

# 3. Verify MCP server
curl -f http://localhost:8000/mcp/health || echo "MCP health check failed"

# 4. Test database connectivity
python -c "
import asyncpg
import asyncio
async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://cguser:password@localhost:5432/claude_guardian')
        await conn.close()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
asyncio.run(test_db())
"
```

---

## 📊 Rollback Impact Assessment

### Before Rollback (Current State)
- Repository size: 315MB
- Python files: 3,857
- Dependencies: 26 core + 56 dev
- Docker services: 3 (PostgreSQL, Qdrant, Redis)

### After Rollback to 5f77206
- Repository size: ~400MB (with dev-archives)
- Python files: ~3,900
- Dependencies: 60+ total
- Docker services: Same 3 + optional app container

---

## 🔍 Troubleshooting Common Issues

### Issue: Services Won't Start
```bash
# Clean Docker state
docker system prune -af
docker volume prune -f

# Remove data and start fresh
rm -rf ./data
docker-compose up -d
```

### Issue: Import Errors After Rollback
```bash
# Fix Python path issues
export PYTHONPATH=/Users/roble/Documents/Python/claude_guardian/src
python -m pip install -e .

# Or use setup.sh
./setup.sh
```

### Issue: Configuration Conflicts
```bash
# Reset all configs to baseline
git checkout 5f77206 -- config/
git checkout 5f77206 -- .env.example

# Manual reconfiguration required
vim .env.example  # Update with your values
cp .env.example .env
```

---

## 🚨 Emergency Contacts & Resources

### Recovery Resources
- **Stable Baseline**: `5f77206` - Repository cleanup with organized artifacts
- **Documentation**: All docs in this commit reflect working state
- **Setup Script**: `./setup.sh` provides one-command deployment

### Quick Recovery Command
```bash
# Nuclear option - complete reset
git reset --hard 5f77206 && \
docker-compose down --volumes && \
rm -rf ./data && \
./setup.sh
```

---

## ✅ Rollback Success Criteria

### Verification Checklist
- [ ] All services start successfully
- [ ] Health checks pass for all endpoints
- [ ] MCP server responds to requests
- [ ] Database connections work
- [ ] No import/module errors in Python
- [ ] Docker containers are healthy
- [ ] Setup.sh completes without errors

---

**⚡ Emergency Priority**: In case of production issues, use hard reset to `5f77206` for immediate stability restoration.