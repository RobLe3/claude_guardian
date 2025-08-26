"""
Administrative API endpoints
System management and configuration
"""

import logging
import os
import psutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..core.security import SecurityManager
from ..core.database import DatabaseManager
from ..core.config import get_settings
# Dependency injection - will be provided by FastAPI

logger = logging.getLogger(__name__)

admin_router = APIRouter()

# Global managers (set by main app)
_db_manager: DatabaseManager = None
_security_manager: SecurityManager = None

def set_managers(db_manager: DatabaseManager, security_manager: SecurityManager):
    """Set global manager instances"""
    global _db_manager, _security_manager
    _db_manager = db_manager
    _security_manager = security_manager

async def get_db_manager() -> DatabaseManager:
    """Get database manager dependency"""
    if not _db_manager:
        raise HTTPException(status_code=503, detail="Database manager not initialized")
    return _db_manager

async def get_security_manager() -> SecurityManager:
    """Get security manager dependency"""
    if not _security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
    return _security_manager


class SystemInfo(BaseModel):
    """System information response"""
    version: str
    uptime: str
    memory_usage: Dict[str, Any]
    cpu_usage: float
    disk_usage: Dict[str, Any]
    active_connections: int


@admin_router.get("/system/info", response_model=SystemInfo)
async def get_system_info():
    """Get comprehensive system information"""
    try:
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent
        }
        
        # CPU information
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percentage": (disk.used / disk.total) * 100
        }
        
        # Network connections (approximate)
        connections = len(psutil.net_connections())
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime = datetime.now() - datetime.fromtimestamp(boot_time)
        
        return SystemInfo(
            version="2.0.0-alpha",
            uptime=str(uptime).split('.')[0],  # Remove microseconds
            memory_usage=memory_info,
            cpu_usage=cpu_usage,
            disk_usage=disk_info,
            active_connections=connections
        )
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


@admin_router.get("/system/health")
async def comprehensive_health_check(
    db_manager: DatabaseManager = Depends(get_db_manager),
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Comprehensive system health check"""
    health_status = {
        "overall": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database health
    try:
        db_health = await db_manager.health_check()
        health_status["components"]["database"] = {
            "status": "healthy" if db_health else "unhealthy",
            "details": "All database connections operational" if db_health else "Database connection issues"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "error",
            "details": str(e)
        }
    
    # Check security manager health
    try:
        security_health = await security_manager.health_check()
        health_status["components"]["security"] = {
            "status": "healthy" if security_health else "unhealthy",
            "details": "Security manager operational" if security_health else "Security manager issues"
        }
    except Exception as e:
        health_status["components"]["security"] = {
            "status": "error",
            "details": str(e)
        }
    
    # Check system resources
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        
        resource_status = "healthy"
        resource_details = []
        
        if memory.percent > 90:
            resource_status = "warning"
            resource_details.append(f"High memory usage: {memory.percent}%")
        
        if cpu > 95:
            resource_status = "warning" 
            resource_details.append(f"High CPU usage: {cpu}%")
        
        if (disk.used / disk.total) > 0.9:
            resource_status = "warning"
            resource_details.append(f"High disk usage: {(disk.used/disk.total)*100:.1f}%")
        
        health_status["components"]["resources"] = {
            "status": resource_status,
            "details": "; ".join(resource_details) if resource_details else "System resources normal"
        }
        
    except Exception as e:
        health_status["components"]["resources"] = {
            "status": "error",
            "details": str(e)
        }
    
    # Determine overall health
    component_statuses = [comp["status"] for comp in health_status["components"].values()]
    
    if "error" in component_statuses:
        health_status["overall"] = "unhealthy"
    elif "unhealthy" in component_statuses:
        health_status["overall"] = "degraded"
    elif "warning" in component_statuses:
        health_status["overall"] = "warning"
    else:
        health_status["overall"] = "healthy"
    
    return health_status


@admin_router.get("/configuration")
async def get_configuration():
    """Get current system configuration (sanitized)"""
    settings = get_settings()
    
    # Return sanitized configuration (no secrets)
    config = settings.to_dict()
    
    # Add runtime information
    config["runtime"] = {
        "python_version": os.sys.version.split()[0],
        "process_id": os.getpid(),
        "working_directory": os.getcwd(),
        "environment_variables": {
            k: v for k, v in os.environ.items() 
            if not any(secret in k.lower() for secret in ['password', 'secret', 'key', 'token'])
        }
    }
    
    return config


@admin_router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days_to_keep: int = 30,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Clean up old data from the database"""
    if days_to_keep < 7:
        raise HTTPException(status_code=400, detail="Must keep at least 7 days of data")
    
    try:
        if not db_manager.postgres_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        async with db_manager.postgres_pool.acquire() as conn:
            # Clean up old security events
            events_deleted = await conn.fetchval("""
                DELETE FROM security_events 
                WHERE timestamp < $1 
                RETURNING COUNT(*)
            """, cutoff_date)
            
            # Clean up old scan results
            scans_deleted = await conn.fetchval("""
                DELETE FROM scan_results 
                WHERE timestamp < $1 
                RETURNING COUNT(*)
            """, cutoff_date)
        
        logger.info(f"Cleanup completed: {events_deleted} events, {scans_deleted} scan results deleted")
        
        return {
            "status": "completed",
            "cutoff_date": cutoff_date.isoformat(),
            "deleted": {
                "security_events": events_deleted or 0,
                "scan_results": scans_deleted or 0
            },
            "total_deleted": (events_deleted or 0) + (scans_deleted or 0)
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@admin_router.get("/logs")
async def get_recent_logs(
    lines: int = 100,
    level: str = "INFO"
):
    """Get recent application logs"""
    # This is a placeholder implementation
    # In production, you'd integrate with your logging system
    return {
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": "This is a placeholder log entry",
                "source": "admin_api"
            }
        ],
        "total_lines": 1,
        "note": "Log integration pending - check /tmp/claude-guardian-v2.log"
    }


@admin_router.post("/system/restart")
async def restart_service():
    """Restart the application service"""
    # This would typically trigger a graceful restart
    # For now, just return a message
    return {
        "status": "restart_requested",
        "message": "Service restart initiated",
        "note": "Manual restart required - stop and start the service"
    }


@admin_router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Export metrics in Prometheus format"""
    # Placeholder for Prometheus metrics
    metrics = """
# HELP claude_guardian_requests_total Total number of requests
# TYPE claude_guardian_requests_total counter
claude_guardian_requests_total 100

# HELP claude_guardian_scan_duration_seconds Duration of security scans
# TYPE claude_guardian_scan_duration_seconds histogram
claude_guardian_scan_duration_seconds_bucket{le="0.1"} 50
claude_guardian_scan_duration_seconds_bucket{le="0.5"} 80
claude_guardian_scan_duration_seconds_bucket{le="1.0"} 95
claude_guardian_scan_duration_seconds_bucket{le="+Inf"} 100

# HELP claude_guardian_threats_detected_total Total number of threats detected
# TYPE claude_guardian_threats_detected_total counter
claude_guardian_threats_detected_total{severity="low"} 25
claude_guardian_threats_detected_total{severity="medium"} 10
claude_guardian_threats_detected_total{severity="high"} 3
claude_guardian_threats_detected_total{severity="critical"} 1
"""
    
    return {"metrics": metrics, "format": "prometheus", "note": "Real metrics implementation pending"}