"""
Security manager for Claude Guardian
Handles authentication, authorization, and security analysis
"""

import asyncio
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import jwt
    from passlib.context import CryptContext
except ImportError:
    jwt = None
    CryptContext = None

from .config import SecurityConfig
from .database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ThreatAnalysis:
    """Results from security analysis"""
    threat_level: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    processing_time_ms: int


@dataclass
class User:
    """User authentication data"""
    id: int
    username: str
    email: str
    roles: List[str]
    is_active: bool = True


class SecurityManager:
    """Manages security operations and authentication"""
    
    def __init__(self, config: SecurityConfig, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.pwd_context = CryptContext(["bcrypt"], deprecated="auto") if CryptContext else None
        
        # Security patterns for threat detection
        self.threat_patterns = {
            "sql_injection": [
                r"(?i)union\s+select",
                r"(?i)or\s+1=1",
                r"(?i)drop\s+table",
                r"(?i)exec\s*\(",
                r"(?i)script\s*>"
            ],
            "xss": [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=",
                r"eval\s*\(",
                r"document\.cookie"
            ],
            "path_traversal": [
                r"\.\.\/",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%252e%252e%252f"
            ],
            "command_injection": [
                r";\s*(cat|ls|pwd|whoami)",
                r"\|\s*(curl|wget|nc)",
                r"`.*`",
                r"\$\(.*\)"
            ],
            "insecure_secrets": [
                r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{1,50}['\"]",
                r"(?i)(api_key|apikey)\s*=\s*['\"][^'\"]{10,}['\"]",
                r"(?i)(secret|token)\s*=\s*['\"][^'\"]{10,}['\"]",
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize security manager"""
        logger.info("🔒 Initializing security manager...")
        
        # Log security manager startup
        if self.db_manager:
            await self.db_manager.log_security_event(
                event_type="security_manager_startup",
                severity="info",
                description="Security manager initialized successfully"
            )
        
        logger.info("✅ Security manager ready")
    
    async def health_check(self) -> bool:
        """Check security manager health"""
        # Verify we can generate and validate tokens
        if not jwt:
            return False
            
        try:
            # Test JWT operations
            test_payload = {"test": True, "exp": datetime.utcnow() + timedelta(seconds=60)}
            token = jwt.encode(test_payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
            decoded = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            return decoded.get("test") is True
        except Exception as e:
            logger.error(f"Security health check failed: {e}")
            return False
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for authenticated user"""
        if not jwt:
            raise RuntimeError("JWT library not available")
            
        payload = {
            "user_id": user.id,
            "username": user.username,
            "roles": user.roles,
            "exp": datetime.utcnow() + timedelta(seconds=self.config.jwt_expiration),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        if not jwt:
            return None
            
        try:
            payload = jwt.decode(
                token, 
                self.config.jwt_secret, 
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    async def analyze_code_security(self, code: str, context: str = "") -> ThreatAnalysis:
        """Perform comprehensive security analysis on code"""
        start_time = datetime.now()
        
        findings = []
        max_severity = "low"
        confidence = 0.0
        
        # Pattern-based threat detection
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                import re
                matches = re.findall(pattern, code)
                if matches:
                    severity = self._get_threat_severity(threat_type, len(matches))
                    finding = {
                        "type": threat_type,
                        "severity": severity,
                        "pattern": pattern,
                        "matches": matches[:5],  # Limit matches for performance
                        "count": len(matches),
                        "description": self._get_threat_description(threat_type)
                    }
                    findings.append(finding)
                    
                    # Update max severity
                    if self._severity_level(severity) > self._severity_level(max_severity):
                        max_severity = severity
                    
                    # Increase confidence based on findings
                    confidence = min(1.0, confidence + 0.15 * len(matches))
        
        # Additional security checks
        security_issues = self._check_security_best_practices(code)
        findings.extend(security_issues)
        
        # Calculate final confidence and threat level
        if not findings:
            threat_level = "low"
            confidence = 0.9  # High confidence in low threat
        else:
            threat_level = max_severity
            confidence = max(0.3, confidence)  # Minimum confidence for findings
        
        recommendations = self._generate_recommendations(findings)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Store analysis results
        if self.db_manager:
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
            await self.db_manager.store_scan_result(
                scan_type="code_security_analysis",
                target_hash=code_hash,
                threat_level=threat_level,
                findings={"findings": findings, "recommendations": recommendations},
                processing_time_ms=processing_time
            )
        
        return ThreatAnalysis(
            threat_level=threat_level,
            confidence=confidence,
            findings=findings,
            recommendations=recommendations,
            processing_time_ms=processing_time
        )
    
    def _get_threat_severity(self, threat_type: str, count: int) -> str:
        """Determine threat severity based on type and count"""
        severity_map = {
            "sql_injection": "high",
            "xss": "medium", 
            "path_traversal": "medium",
            "command_injection": "critical",
            "insecure_secrets": "high"
        }
        
        base_severity = severity_map.get(threat_type, "low")
        
        # Escalate severity based on count
        if count >= 5:
            if base_severity == "medium":
                return "high"
            elif base_severity == "high":
                return "critical"
        
        return base_severity
    
    def _severity_level(self, severity: str) -> int:
        """Convert severity to numeric level for comparison"""
        levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return levels.get(severity, 0)
    
    def _get_threat_description(self, threat_type: str) -> str:
        """Get human-readable description for threat type"""
        descriptions = {
            "sql_injection": "Potential SQL injection vulnerability detected",
            "xss": "Cross-site scripting (XSS) vulnerability found",
            "path_traversal": "Path traversal attack pattern identified",
            "command_injection": "Command injection vulnerability detected",
            "insecure_secrets": "Hardcoded secrets or credentials found"
        }
        return descriptions.get(threat_type, "Security issue detected")
    
    def _check_security_best_practices(self, code: str) -> List[Dict[str, Any]]:
        """Check for security best practices violations"""
        issues = []
        
        # Check for eval usage
        if "eval(" in code:
            issues.append({
                "type": "insecure_function",
                "severity": "high",
                "pattern": "eval() usage",
                "description": "Use of eval() function can lead to code injection",
                "matches": ["eval()"],
                "count": code.count("eval(")
            })
        
        # Check for weak randomization
        if "Math.random()" in code or "random.random()" in code:
            issues.append({
                "type": "weak_cryptography",
                "severity": "medium",
                "pattern": "weak_random",
                "description": "Weak randomization detected, use cryptographically secure random",
                "matches": ["Math.random()" if "Math.random()" in code else "random.random()"],
                "count": 1
            })
        
        return issues
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        threat_types = {f["type"] for f in findings}
        
        if "sql_injection" in threat_types:
            recommendations.append("Use parameterized queries or prepared statements")
            recommendations.append("Implement input validation and sanitization")
        
        if "xss" in threat_types:
            recommendations.append("Sanitize user input and encode output")
            recommendations.append("Use Content Security Policy (CSP) headers")
        
        if "insecure_secrets" in threat_types:
            recommendations.append("Use environment variables or secure vaults for secrets")
            recommendations.append("Never hardcode credentials in source code")
        
        if "command_injection" in threat_types:
            recommendations.append("Avoid executing user input as system commands")
            recommendations.append("Use allowlists for permitted inputs")
        
        if not recommendations:
            recommendations.append("Continue following security best practices")
        
        return recommendations