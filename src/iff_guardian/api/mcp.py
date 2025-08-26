"""
MCP (Model Context Protocol) API endpoints
Provides security analysis tools for Claude Code integration
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..core.security import SecurityManager, ThreatAnalysis
from ..core.database import DatabaseManager
# Dependency injection - will be provided by FastAPI

logger = logging.getLogger(__name__)

mcp_router = APIRouter()

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


class SecurityScanRequest(BaseModel):
    """Request model for security scanning"""
    code: str = Field(..., description="Code to analyze for security issues")
    context: str = Field("", description="Optional context about the code")
    scan_type: str = Field("comprehensive", description="Type of scan to perform")


class SecurityScanResponse(BaseModel):
    """Response model for security scan results"""
    threat_level: str
    confidence: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    processing_time_ms: int
    scan_id: str


class MCPToolInfo(BaseModel):
    """Information about available MCP tools"""
    name: str
    description: str
    parameters: Dict[str, Any]


@mcp_router.get("/tools", response_model=List[MCPToolInfo])
async def list_mcp_tools():
    """List available MCP security tools"""
    tools = [
        {
            "name": "scan_code_security",
            "description": "Analyze code for security vulnerabilities and threats",
            "parameters": {
                "code": {
                    "type": "string",
                    "description": "Source code to analyze"
                },
                "context": {
                    "type": "string", 
                    "description": "Optional context about the code",
                    "required": False
                }
            }
        },
        {
            "name": "check_dependencies",
            "description": "Scan dependencies for known vulnerabilities",
            "parameters": {
                "dependencies": {
                    "type": "array",
                    "description": "List of dependencies to check"
                }
            }
        },
        {
            "name": "analyze_network_config",
            "description": "Review network configuration for security issues",
            "parameters": {
                "config": {
                    "type": "string",
                    "description": "Network configuration to analyze"
                }
            }
        },
        {
            "name": "audit_permissions",
            "description": "Audit file and system permissions",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "Path to audit permissions for"
                }
            }
        },
        {
            "name": "detect_secrets",
            "description": "Scan for hardcoded secrets and credentials",
            "parameters": {
                "content": {
                    "type": "string",
                    "description": "Content to scan for secrets"
                }
            }
        }
    ]
    return [MCPToolInfo(**tool) for tool in tools]


@mcp_router.post("/scan/security", response_model=SecurityScanResponse)
async def scan_code_security(
    request: SecurityScanRequest,
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Perform comprehensive security analysis on code"""
    try:
        logger.info(f"Starting security scan: {len(request.code)} characters")
        
        # Perform security analysis
        analysis = await security_manager.analyze_code_security(
            code=request.code,
            context=request.context
        )
        
        # Generate scan ID for tracking
        import hashlib
        import uuid
        scan_id = str(uuid.uuid4())[:8]
        
        response = SecurityScanResponse(
            threat_level=analysis.threat_level,
            confidence=analysis.confidence,
            findings=analysis.findings,
            recommendations=analysis.recommendations,
            processing_time_ms=analysis.processing_time_ms,
            scan_id=scan_id
        )
        
        logger.info(f"Security scan completed: {analysis.threat_level} threat level, {len(analysis.findings)} findings")
        return response
        
    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")


@mcp_router.post("/scan/dependencies")
async def scan_dependencies(
    dependencies: List[str],
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Scan dependencies for known vulnerabilities"""
    # Placeholder implementation - would integrate with vulnerability databases
    results = []
    
    for dep in dependencies:
        # Simulate vulnerability check
        result = {
            "name": dep,
            "version": "unknown",
            "vulnerabilities": [],
            "risk_level": "low",
            "recommendations": ["Keep dependencies updated"]
        }
        results.append(result)
    
    return {"dependencies": results, "summary": {"total": len(dependencies), "vulnerable": 0}}


@mcp_router.post("/analyze/network")
async def analyze_network_config(
    config: str,
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Analyze network configuration for security issues"""
    # Placeholder implementation for network config analysis
    findings = []
    
    # Check for common misconfigurations
    if "password" in config.lower():
        findings.append({
            "type": "credential_exposure",
            "severity": "high",
            "description": "Potential credential exposure in configuration"
        })
    
    return {
        "analysis_type": "network_configuration",
        "findings": findings,
        "risk_score": 2.5 if findings else 1.0,
        "recommendations": ["Review configuration for security best practices"]
    }


@mcp_router.post("/audit/permissions")
async def audit_permissions(
    path: str,
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Audit file and directory permissions"""
    # Placeholder implementation for permission auditing
    return {
        "path": path,
        "permissions": "755",
        "owner": "user",
        "group": "user",
        "issues": [],
        "recommendations": ["Follow principle of least privilege"]
    }


@mcp_router.post("/detect/secrets")
async def detect_secrets(
    content: str,
    security_manager: SecurityManager = Depends(get_security_manager)
):
    """Detect hardcoded secrets and credentials in content"""
    try:
        # Use the security manager's secret detection
        analysis = await security_manager.analyze_code_security(content, "secret_detection")
        
        # Filter for secret-related findings
        secret_findings = [
            f for f in analysis.findings 
            if f.get("type") == "insecure_secrets"
        ]
        
        return {
            "secrets_found": len(secret_findings),
            "findings": secret_findings,
            "severity": "high" if secret_findings else "low",
            "recommendations": [
                "Remove hardcoded secrets",
                "Use environment variables or secret management systems",
                "Scan repositories for exposed credentials"
            ] if secret_findings else ["No secrets detected"]
        }
        
    except Exception as e:
        logger.error(f"Secret detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Secret detection failed: {str(e)}")


@mcp_router.get("/health")
async def mcp_health_check():
    """Health check endpoint for MCP service"""
    return {
        "service": "mcp_api",
        "status": "healthy",
        "tools_available": 5,
        "version": "2.0.0-alpha"
    }