"""
Configuration management for Claude Guardian
Handles environment variables, secrets, and service discovery
"""

import os
import secrets
from dataclasses import dataclass
from typing import Optional
import logging
from urllib.parse import urlparse


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    postgres_url: str
    qdrant_url: str
    redis_url: str
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            postgres_url=os.getenv(
                "DATABASE_URL", 
                "postgresql+asyncpg://cguser:CHANGE_THIS_SECURE_PASSWORD_123!@localhost:5432/claude_guardian"
            ),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )


@dataclass  
class SecurityConfig:
    """Security and authentication configuration"""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        # Generate secure JWT secret if not provided
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret or jwt_secret in ["your-secret-key", "change-me"]:
            jwt_secret = secrets.token_urlsafe(32)
            
        return cls(
            jwt_secret=jwt_secret,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration=int(os.getenv("JWT_EXPIRATION", "3600")),
            bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        )


@dataclass
class ServiceConfig:
    """Microservices configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    debug: bool = False
    environment: str = "production"
    
    @classmethod
    def from_env(cls) -> "ServiceConfig":
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            workers=int(os.getenv("WORKERS", "4")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "production")
        )


@dataclass
class MCPConfig:
    """MCP (Model Context Protocol) configuration"""
    port: int = 8083
    host: str = "0.0.0.0"
    max_connections: int = 100
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        return cls(
            port=int(os.getenv("MCP_PORT", "8000")),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            max_connections=int(os.getenv("MCP_MAX_CONNECTIONS", "100")),
            timeout=int(os.getenv("MCP_TIMEOUT", "30"))
        )


@dataclass
class ThreatAnalysisConfig:
    """Threat analysis and security configuration"""
    detection_threshold: float = 0.75
    max_scan_size: int = 1024 * 1024  # 1MB
    enable_ml_analysis: bool = True
    enable_vector_search: bool = True
    vector_similarity_threshold: float = 0.8
    
    @classmethod
    def from_env(cls) -> "ThreatAnalysisConfig":
        return cls(
            detection_threshold=float(os.getenv("DETECTION_THRESHOLD", "0.75")),
            max_scan_size=int(os.getenv("MAX_SCAN_SIZE", str(1024 * 1024))),
            enable_ml_analysis=os.getenv("ENABLE_ML_ANALYSIS", "true").lower() == "true",
            enable_vector_search=os.getenv("ENABLE_VECTOR_SEARCH", "true").lower() == "true",
            vector_similarity_threshold=float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.8"))
        )


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_debug_logging: bool = False
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            enable_debug_logging=os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true"
        )


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    environment: str = "production"
    development_mode: bool = False
    guardian_mode: str = "full"
    security_level: str = "moderate"
    
    @classmethod 
    def from_env(cls) -> "EnvironmentConfig":
        return cls(
            environment=os.getenv("ENVIRONMENT", "production"),
            development_mode=os.getenv("DEVELOPMENT_MODE", "false").lower() == "true",
            guardian_mode=os.getenv("GUARDIAN_MODE", "full"),
            security_level=os.getenv("SECURITY_LEVEL", "moderate")
        )


@dataclass
class Settings:
    """Main application settings"""
    database: DatabaseConfig
    security: SecurityConfig
    service: ServiceConfig
    mcp: MCPConfig
    threat_analysis: ThreatAnalysisConfig
    logging: LoggingConfig
    environment: EnvironmentConfig
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load all configuration from environment variables"""
        return cls(
            database=DatabaseConfig.from_env(),
            security=SecurityConfig.from_env(),
            service=ServiceConfig.from_env(),
            mcp=MCPConfig.from_env(),
            threat_analysis=ThreatAnalysisConfig.from_env(),
            logging=LoggingConfig.from_env(),
            environment=EnvironmentConfig.from_env()
        )
    
    def validate(self) -> None:
        """Validate configuration settings"""
        # Validate database URLs
        for url_name, url in [
            ("DATABASE_URL", self.database.postgres_url),
            ("QDRANT_URL", self.database.qdrant_url),
            ("REDIS_URL", self.database.redis_url)
        ]:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid {url_name}: {url}")
        
        # Validate security settings
        if len(self.security.jwt_secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
            
        if self.security.bcrypt_rounds < 10:
            raise ValueError("BCrypt rounds must be at least 10")
            
        # Validate service settings
        if not (1 <= self.service.port <= 65535):
            raise ValueError(f"Invalid port: {self.service.port}")
            
        if not (1 <= self.mcp.port <= 65535):
            raise ValueError(f"Invalid MCP port: {self.mcp.port}")
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary (for logging/debugging)"""
        return {
            "database": {
                "postgres_host": urlparse(self.database.postgres_url).netloc,
                "qdrant_url": self.database.qdrant_url,
                "redis_host": urlparse(self.database.redis_url).netloc
            },
            "security": {
                "jwt_algorithm": self.security.jwt_algorithm,
                "bcrypt_rounds": self.security.bcrypt_rounds
            },
            "service": {
                "host": self.service.host,
                "port": self.service.port,
                "environment": self.service.environment
            },
            "mcp": {
                "port": self.mcp.port,
                "max_connections": self.mcp.max_connections
            },
            "threat_analysis": {
                "detection_threshold": self.threat_analysis.detection_threshold,
                "enable_ml_analysis": self.threat_analysis.enable_ml_analysis
            },
            "logging": {
                "level": self.logging.level,
                "enable_debug_logging": self.logging.enable_debug_logging
            },
            "environment": {
                "environment": self.environment.environment,
                "development_mode": self.environment.development_mode,
                "guardian_mode": self.environment.guardian_mode,
                "security_level": self.environment.security_level
            }
        }


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (singleton pattern)"""
    global settings
    if settings is None:
        settings = Settings.from_env()
        settings.validate()
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)"""
    global settings
    settings = Settings.from_env()
    settings.validate()
    return settings