"""
Centralized dependency injection for Claude Guardian
Provides FastAPI-compatible dependency functions for manager instances
"""

from typing import Optional
from fastapi import HTTPException

from .database import DatabaseManager
from .security import SecurityManager


class ManagerRegistry:
    """Central registry for manager instances"""
    
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.security_manager: Optional[SecurityManager] = None
    
    def set_managers(self, db_manager: DatabaseManager, security_manager: SecurityManager):
        """Set manager instances in the registry"""
        self.db_manager = db_manager
        self.security_manager = security_manager
    
    def clear_managers(self):
        """Clear all manager instances (useful for testing)"""
        self.db_manager = None
        self.security_manager = None


# Global registry instance
_registry = ManagerRegistry()


def set_managers(db_manager: DatabaseManager, security_manager: SecurityManager):
    """Set global manager instances"""
    _registry.set_managers(db_manager, security_manager)


def clear_managers():
    """Clear all manager instances (useful for testing)"""
    _registry.clear_managers()


async def get_db_manager() -> DatabaseManager:
    """Get database manager dependency for FastAPI"""
    if not _registry.db_manager:
        raise HTTPException(status_code=503, detail="Database manager not initialized")
    return _registry.db_manager


async def get_security_manager() -> SecurityManager:
    """Get security manager dependency for FastAPI"""
    if not _registry.security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
    return _registry.security_manager


def get_registry() -> ManagerRegistry:
    """Get the manager registry (for testing and advanced use cases)"""
    return _registry