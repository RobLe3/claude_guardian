"""
Claude Guardian - Enterprise Security Platform for Claude Code
Version 2.0.0 - Complete Implementation
"""

__version__ = "2.0.0-alpha"
__author__ = "Claude Guardian Team"
__description__ = "Enterprise-grade security analysis platform with Claude Code integration"

from .core.config import Settings
from .core.security import SecurityManager
from .core.database import DatabaseManager

__all__ = [
    "Settings",
    "SecurityManager", 
    "DatabaseManager",
    "__version__"
]