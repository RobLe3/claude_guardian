#!/usr/bin/env python3
"""
Health check script for Claude Guardian Docker container.
This script performs comprehensive health checks including:
- Application responsiveness
- Database connectivity
- Redis connectivity
- System resources
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any
import httpx
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = os.getenv('PORT', '8000')
        self.timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        # Health check thresholds
        self.max_memory_percent = float(os.getenv('MAX_MEMORY_PERCENT', '90'))
        self.max_cpu_percent = float(os.getenv('MAX_CPU_PERCENT', '95'))
        
    async def check_application_health(self) -> Dict[str, Any]:
        """Check if the application is responding to HTTP requests."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"http://{self.host}:{self.port}/health")
                
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status_code}',
                        'status_code': response.status_code
                    }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity."""
        if not self.database_url:
            return {'status': 'skipped', 'reason': 'DATABASE_URL not configured'}
        
        try:
            import asyncpg
            
            conn = await asyncpg.connect(self.database_url)
            await conn.execute('SELECT 1')
            await conn.close()
            
            return {'status': 'healthy'}
        except ImportError:
            return {'status': 'skipped', 'reason': 'asyncpg not available'}
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_redis_connectivity(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        if not self.redis_url:
            return {'status': 'skipped', 'reason': 'REDIS_URL not configured'}
        
        try:
            import redis.asyncio as redis
            
            client = redis.from_url(self.redis_url)
            await client.ping()
            await client.close()
            
            return {'status': 'healthy'}
        except ImportError:
            return {'status': 'skipped', 'reason': 'redis not available'}
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage for root partition
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            status = 'healthy'
            issues = []
            
            if memory_percent > self.max_memory_percent:
                status = 'unhealthy'
                issues.append(f'High memory usage: {memory_percent:.1f}%')
            
            if cpu_percent > self.max_cpu_percent:
                status = 'unhealthy'
                issues.append(f'High CPU usage: {cpu_percent:.1f}%')
            
            return {
                'status': status,
                'memory_percent': round(memory_percent, 1),
                'cpu_percent': round(cpu_percent, 1),
                'disk_percent': round(disk_percent, 1),
                'issues': issues
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Check critical file and directory permissions."""
        critical_paths = [
            '/var/log/claude-guardian',
            '/var/lib/claude-guardian',
            '/tmp/uploads'
        ]
        
        issues = []
        
        for path in critical_paths:
            if os.path.exists(path):
                if not os.access(path, os.R_OK | os.W_OK):
                    issues.append(f'Insufficient permissions for {path}')
            else:
                issues.append(f'Missing directory: {path}')
        
        return {
            'status': 'healthy' if not issues else 'unhealthy',
            'issues': issues
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive results."""
        start_time = time.time()
        
        # Run checks concurrently where possible
        app_health, db_health, redis_health = await asyncio.gather(
            self.check_application_health(),
            self.check_database_connectivity(),
            self.check_redis_connectivity(),
            return_exceptions=True
        )
        
        # Run synchronous checks
        system_health = self.check_system_resources()
        permissions_health = self.check_file_permissions()
        
        # Handle exceptions from async checks
        if isinstance(app_health, Exception):
            app_health = {'status': 'error', 'error': str(app_health)}
        if isinstance(db_health, Exception):
            db_health = {'status': 'error', 'error': str(db_health)}
        if isinstance(redis_health, Exception):
            redis_health = {'status': 'error', 'error': str(redis_health)}
        
        # Determine overall health
        checks = {
            'application': app_health,
            'database': db_health,
            'redis': redis_health,
            'system': system_health,
            'permissions': permissions_health
        }
        
        # Overall status logic
        unhealthy_checks = [
            name for name, check in checks.items()
            if check.get('status') == 'unhealthy'
        ]
        
        error_checks = [
            name for name, check in checks.items()
            if check.get('status') == 'error'
        ]
        
        if unhealthy_checks or error_checks:
            overall_status = 'unhealthy'
        else:
            overall_status = 'healthy'
        
        return {
            'status': overall_status,
            'timestamp': time.time(),
            'duration_ms': round((time.time() - start_time) * 1000, 2),
            'checks': checks,
            'summary': {
                'unhealthy_checks': unhealthy_checks,
                'error_checks': error_checks
            }
        }

async def main():
    """Main health check function."""
    checker = HealthChecker()
    
    try:
        results = await checker.run_all_checks()
        
        # Output results as JSON for structured logging
        print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        if results['status'] == 'healthy':
            logger.info("Health check passed")
            sys.exit(0)
        else:
            logger.error(f"Health check failed: {results['summary']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        print(json.dumps({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    # Handle the case where asyncio might not be available
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to run health check: {e}")
        sys.exit(1)