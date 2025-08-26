"""
Security API endpoints
Provides direct access to security analysis capabilities
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ..core.security import SecurityManager, ThreatAnalysis
from ..core.database import DatabaseManager
# Dependency injection - will be provided by FastAPI

logger = logging.getLogger(__name__)

security_router = APIRouter()

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


class SecurityEventRequest(BaseModel):
    """Request to log a security event"""
    event_type: str
    severity: str
    description: str
    metadata: Optional[Dict[str, Any]] = None


class ThreatIntelligenceQuery(BaseModel):
    """Query for threat intelligence"""
    threat_type: str
    confidence_threshold: float = 0.7
    limit: int = 100


@security_router.post("/events")
async def log_security_event(
    event: SecurityEventRequest,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Log a security event"""
    try:
        await db_manager.log_security_event(
            event_type=event.event_type,
            severity=event.severity,
            description=event.description,
            metadata=event.metadata
        )
        
        logger.info(f"Security event logged: {event.event_type} - {event.severity}")
        return {"status": "logged", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log security event")


@security_router.get("/events")
async def get_security_events(
    limit: int = Query(50, ge=1, le=1000),
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Retrieve recent security events"""
    try:
        if not db_manager.postgres_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Build query based on filters
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        
        if severity:
            query += " AND severity = $" + str(len(params) + 1)
            params.append(severity)
            
        if event_type:
            query += " AND event_type = $" + str(len(params) + 1)
            params.append(event_type)
        
        query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        events = [dict(row) for row in rows]
        
        return {
            "events": events,
            "count": len(events),
            "filters": {"severity": severity, "event_type": event_type}
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve security events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security events")


@security_router.get("/scan-results")
async def get_scan_results(
    limit: int = Query(20, ge=1, le=100),
    threat_level: Optional[str] = Query(None),
    scan_type: Optional[str] = Query(None),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Retrieve recent scan results"""
    try:
        if not db_manager.postgres_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        query = "SELECT * FROM scan_results WHERE 1=1"
        params = []
        
        if threat_level:
            query += " AND threat_level = $" + str(len(params) + 1)
            params.append(threat_level)
            
        if scan_type:
            query += " AND scan_type = $" + str(len(params) + 1)
            params.append(scan_type)
        
        query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        results = []
        for row in rows:
            result = dict(row)
            # Convert timestamp to ISO format
            if result.get('timestamp'):
                result['timestamp'] = result['timestamp'].isoformat()
            results.append(result)
        
        return {
            "scan_results": results,
            "count": len(results),
            "filters": {"threat_level": threat_level, "scan_type": scan_type}
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve scan results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scan results")


@security_router.get("/statistics")
async def get_security_statistics(
    days: int = Query(7, ge=1, le=90),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get security statistics and metrics"""
    try:
        if not db_manager.postgres_pool:
            return {
                "events_by_severity": {},
                "scans_by_threat_level": {},
                "total_events": 0,
                "total_scans": 0,
                "period_days": days,
                "note": "Database not available"
            }
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with db_manager.postgres_pool.acquire() as conn:
            # Get events by severity
            events_query = """
                SELECT severity, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp >= $1 
                GROUP BY severity
            """
            event_rows = await conn.fetch(events_query, start_date)
            events_by_severity = {row['severity']: row['count'] for row in event_rows}
            
            # Get scans by threat level
            scans_query = """
                SELECT threat_level, COUNT(*) as count 
                FROM scan_results 
                WHERE timestamp >= $1 
                GROUP BY threat_level
            """
            scan_rows = await conn.fetch(scans_query, start_date)
            scans_by_threat_level = {row['threat_level']: row['count'] for row in scan_rows}
            
            # Get totals
            total_events = await conn.fetchval(
                "SELECT COUNT(*) FROM security_events WHERE timestamp >= $1", 
                start_date
            )
            total_scans = await conn.fetchval(
                "SELECT COUNT(*) FROM scan_results WHERE timestamp >= $1", 
                start_date
            )
        
        return {
            "events_by_severity": events_by_severity,
            "scans_by_threat_level": scans_by_threat_level,
            "total_events": total_events or 0,
            "total_scans": total_scans or 0,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate statistics")


@security_router.post("/analyze/bulk")
async def bulk_security_analysis(
    requests: List[Dict[str, Any]],
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Perform bulk security analysis on multiple items"""
    if len(requests) > 10:  # Limit bulk operations
        raise HTTPException(status_code=400, detail="Maximum 10 items per bulk request")
    
    results = []
    
    for i, req in enumerate(requests):
        try:
            code = req.get("code", "")
            context = req.get("context", f"bulk_item_{i}")
            
            analysis = await security_manager.analyze_code_security(code, context)
            
            result = {
                "item_id": i,
                "threat_level": analysis.threat_level,
                "confidence": analysis.confidence,
                "findings_count": len(analysis.findings),
                "processing_time_ms": analysis.processing_time_ms
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"Bulk analysis item {i} failed: {e}")
            results.append({
                "item_id": i,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "results": results,
        "summary": {
            "total_items": len(requests),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r])
        }
    }


@security_router.get("/patterns")
async def get_threat_patterns(
    pattern_type: Optional[str] = Query(None),
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Get threat detection patterns"""
    patterns = security_manager.threat_patterns
    
    if pattern_type and pattern_type in patterns:
        return {
            "pattern_type": pattern_type,
            "patterns": patterns[pattern_type],
            "count": len(patterns[pattern_type])
        }
    
    return {
        "all_patterns": {
            name: {"count": len(patterns), "patterns": patterns} 
            for name, patterns in patterns.items()
        },
        "total_types": len(patterns),
        "total_patterns": sum(len(p) for p in patterns.values())
    }