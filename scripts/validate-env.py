#!/usr/bin/env python3
"""
Environment Variable Validation Script for Claude Guardian
Validates that all required environment variables are properly configured.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    print("Warning: python-dotenv not available, .env file will not be loaded")


class EnvironmentValidator:
    """Validates environment variables for Claude Guardian"""
    
    # Required environment variables for basic operation
    REQUIRED_VARS = [
        "ENVIRONMENT",
        "HOST", 
        "PORT",
        "MCP_PORT",
        "SECURITY_LEVEL",
        "LOG_LEVEL"
    ]
    
    # Required for production deployments
    PRODUCTION_REQUIRED = [
        "JWT_SECRET",
        "DATABASE_URL",
        "REDIS_URL", 
        "QDRANT_URL"
    ]
    
    # Optional but recommended
    RECOMMENDED_VARS = [
        "GUARDIAN_MODE",
        "DEVELOPMENT_MODE",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD"
    ]
    
    # Security validations
    SECURITY_VALIDATIONS = {
        "JWT_SECRET": {"min_length": 32, "not_defaults": ["your-secret-key", "change-me", "dev-secret-key-not-for-production"]},
        "POSTGRES_PASSWORD": {"min_length": 16, "not_defaults": ["password", "your_secure_password", "CHANGE_THIS_SECURE_PASSWORD_123!"]},
        "REDIS_PASSWORD": {"min_length": 16, "not_defaults": ["password", "your_redis_password", "CHANGE_THIS_REDIS_PASSWORD_123!"]}
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.env_vars = dict(os.environ)
        
    def validate_required_vars(self) -> None:
        """Validate that all required environment variables are set"""
        missing_vars = []
        
        for var in self.REQUIRED_VARS:
            if not self.env_vars.get(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
            
    def validate_production_vars(self) -> None:
        """Validate production-specific environment variables"""
        environment = self.env_vars.get("ENVIRONMENT", "").lower()
        
        if environment == "production":
            missing_vars = []
            for var in self.PRODUCTION_REQUIRED:
                if not self.env_vars.get(var):
                    missing_vars.append(var)
                    
            if missing_vars:
                self.errors.append(f"Missing production environment variables: {', '.join(missing_vars)}")
                
    def validate_recommended_vars(self) -> None:
        """Check for recommended environment variables"""
        missing_vars = []
        
        for var in self.RECOMMENDED_VARS:
            if not self.env_vars.get(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.warnings.append(f"Missing recommended environment variables: {', '.join(missing_vars)}")
            
    def validate_security(self) -> None:
        """Validate security-related environment variables"""
        for var, rules in self.SECURITY_VALIDATIONS.items():
            value = self.env_vars.get(var)
            if not value:
                continue
                
            # Check minimum length
            if len(value) < rules["min_length"]:
                self.errors.append(f"{var} must be at least {rules['min_length']} characters long")
                
            # Check against default values
            if value in rules["not_defaults"]:
                self.errors.append(f"{var} is using a default/insecure value - please change it")
                
    def validate_urls(self) -> None:
        """Validate URL format for database connections"""
        url_vars = ["DATABASE_URL", "REDIS_URL", "QDRANT_URL"]
        
        for var in url_vars:
            url = self.env_vars.get(var)
            if not url:
                continue
                
            try:
                parsed = urlparse(url)
                if not parsed.scheme:
                    self.errors.append(f"{var} missing URL scheme (http/https/postgresql/redis)")
                if not parsed.netloc:
                    self.errors.append(f"{var} missing host/port information")
            except Exception as e:
                self.errors.append(f"{var} has invalid URL format: {e}")
                
    def validate_ports(self) -> None:
        """Validate port numbers"""
        port_vars = ["PORT", "MCP_PORT"]
        
        for var in port_vars:
            port_str = self.env_vars.get(var)
            if not port_str:
                continue
                
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    self.errors.append(f"{var} must be between 1 and 65535")
            except ValueError:
                self.errors.append(f"{var} must be a valid integer")
                
    def validate_enums(self) -> None:
        """Validate enumerated values"""
        enum_validations = {
            "ENVIRONMENT": ["development", "staging", "production"],
            "SECURITY_LEVEL": ["strict", "moderate", "permissive"],
            "LOG_LEVEL": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "GUARDIAN_MODE": ["full", "mcp_only", "api_only"]
        }
        
        for var, valid_values in enum_validations.items():
            value = self.env_vars.get(var)
            if value and value not in valid_values:
                self.errors.append(f"{var} must be one of: {', '.join(valid_values)}")
                
    def validate_boolean_vars(self) -> None:
        """Validate boolean environment variables"""
        boolean_vars = [
            "DEBUG", "DEVELOPMENT_MODE", "ENABLE_MONITORING", 
            "ENABLE_DEBUG_LOGGING", "GDPR_ENABLED"
        ]
        
        for var in boolean_vars:
            value = self.env_vars.get(var)
            if value and value.lower() not in ["true", "false"]:
                self.warnings.append(f"{var} should be 'true' or 'false', got: {value}")
                
    def check_sensitive_data(self) -> None:
        """Check for sensitive data that might be accidentally exposed"""
        sensitive_patterns = [
            "password", "secret", "key", "token", "credential"
        ]
        
        for var, value in self.env_vars.items():
            if any(pattern in var.lower() for pattern in sensitive_patterns):
                if len(value) < 8:
                    self.warnings.append(f"{var} appears to be sensitive but is very short")
                    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating Claude Guardian environment variables...")
        print("=" * 60)
        
        # Run all validation checks
        self.validate_required_vars()
        self.validate_production_vars()
        self.validate_recommended_vars()
        self.validate_security()
        self.validate_urls()
        self.validate_ports()
        self.validate_enums()
        self.validate_boolean_vars()
        self.check_sensitive_data()
        
        # Report results
        if self.errors:
            print("❌ VALIDATION ERRORS:")
            for error in self.errors:
                print(f"   • {error}")
            print()
            
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
            
        # Summary
        total_vars_checked = len([v for v in self.REQUIRED_VARS + self.PRODUCTION_REQUIRED if self.env_vars.get(v)])
        
        print(f"📊 VALIDATION SUMMARY:")
        print(f"   • Environment variables checked: {total_vars_checked}")
        print(f"   • Errors found: {len(self.errors)}")
        print(f"   • Warnings: {len(self.warnings)}")
        print(f"   • Current environment: {self.env_vars.get('ENVIRONMENT', 'not set')}")
        
        if not self.errors:
            print("✅ Environment validation passed!")
            return True
        else:
            print("❌ Environment validation failed!")
            return False


def main():
    """Main validation script"""
    validator = EnvironmentValidator()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Create one from .env.template:")
        print("   cp .env.template .env")
        print()
        
    success = validator.run_validation()
    
    if not success:
        print("\n💡 To fix these issues:")
        print("   1. Copy .env.template to .env if you haven't already")
        print("   2. Generate secure passwords: openssl rand -base64 32")
        print("   3. Update the configuration values as needed")
        print("   4. Run this script again to validate")
        sys.exit(1)
    else:
        print("\n🚀 Environment is properly configured!")
        sys.exit(0)


if __name__ == "__main__":
    main()