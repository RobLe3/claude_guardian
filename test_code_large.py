# Large test code sample (100KB+)
import os
import sys
import subprocess
import hashlib
import base64
import json
import pickle
import urllib.request
import sqlite3
import tempfile
import threading
import socket
import ssl
import xml.etree.ElementTree as ET
import yaml
import requests
from datetime import datetime
import logging
import re

# Large-scale security testing framework with multiple vulnerabilities
class ComprehensiveSecurityTestSuite:
    """
    A comprehensive test suite containing various security vulnerabilities
    for testing Claude Guardian's performance with large codebases.
    """
    
    def __init__(self):
        # Configuration with hardcoded secrets (vulnerability)
        self.config = {
            "api_keys": {
                "aws": "AKIA" + "EXAMPLE" + "KEY123",  # AWS key pattern (obfuscated for testing)
                "stripe": "sk_test_" + "EXAMPLE" + "KEY456",  # Stripe key (obfuscated for testing)
                "github": "ghp_" + "EXAMPLE" + "TOKEN789",  # GitHub token (obfuscated for testing)
                "slack": "xoxb-" + "EXAMPLE" + "BOT012",  # Slack bot token (obfuscated for testing)
                "jwt_secret": "super_secret_jwt_key_2023_production",
                "encryption_key": "AES256_ENCRYPTION_KEY_DO_NOT_SHARE_2023"
            },
            "database": {
                "host": "production-db.company.com",
                "port": 5432,
                "username": "postgres_admin",
                "password": "prod_db_password_2023!",  # Hardcoded password
                "ssl_mode": "disable"  # Insecure SSL configuration
            },
            "redis": {
                "host": "redis.internal.company.com", 
                "port": 6379,
                "password": "redis_cache_pwd_123",
                "ssl": False  # Insecure Redis connection
            },
            "smtp": {
                "server": "smtp.company.com",
                "port": 587,
                "username": "noreply@company.com",
                "password": "email_service_password_2023"  # Email password
            }
        }
        
        # Logging configuration that might leak sensitive data
        logging.basicConfig(level=logging.DEBUG)  # Debug logging in production
        self.logger = logging.getLogger(__name__)
        
    def command_injection_vulnerabilities(self, user_inputs):
        """Multiple command injection patterns"""
        results = []
        
        for user_input in user_inputs:
            # Pattern 1: Direct os.system usage
            os.system(f"ping -c 1 {user_input}")
            
            # Pattern 2: subprocess with shell=True
            subprocess.run(f"curl {user_input}", shell=True)
            
            # Pattern 3: subprocess.call
            subprocess.call(["sh", "-c", f"wget {user_input}"])
            
            # Pattern 4: os.popen
            result = os.popen(f"dig {user_input}").read()
            results.append(result)
            
            # Pattern 5: eval with os commands
            eval(f"os.system('echo {user_input}')")
            
        return results
    
    def sql_injection_vulnerabilities(self, user_data):
        """Multiple SQL injection patterns"""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                password_hash TEXT,
                is_admin BOOLEAN
            )
        """)
        
        # Vulnerable patterns
        for data in user_data:
            # Pattern 1: String concatenation
            query1 = f"SELECT * FROM users WHERE username = '{data['username']}'"
            cursor.execute(query1)
            
            # Pattern 2: .format() usage
            query2 = "SELECT * FROM users WHERE email = '{}'".format(data['email'])
            cursor.execute(query2)
            
            # Pattern 3: % formatting
            query3 = "SELECT * FROM users WHERE id = %s" % data['user_id']
            cursor.execute(query3)
            
            # Pattern 4: Multiple parameter injection
            query4 = f"UPDATE users SET username='{data['username']}', email='{data['email']}' WHERE id={data['user_id']}"
            cursor.execute(query4)
        
        return cursor.fetchall()
    
    def path_traversal_vulnerabilities(self, filenames):
        """Path traversal attack vectors"""
        results = []
        
        for filename in filenames:
            try:
                # Pattern 1: Direct file access
                with open(f"/var/www/uploads/{filename}", 'r') as f:
                    content = f.read()
                    results.append(content)
                
                # Pattern 2: os.path.join without validation
                file_path = os.path.join("/var/www/static", filename)
                with open(file_path, 'r') as f:
                    results.append(f.read())
                
                # Pattern 3: Template inclusion
                template_path = f"/app/templates/{filename}.html"
                with open(template_path, 'r') as f:
                    results.append(f.read())
                    
            except FileNotFoundError:
                results.append(f"File not found: {filename}")
            except Exception as e:
                results.append(f"Error accessing {filename}: {str(e)}")
        
        return results
    
    def insecure_deserialization(self, serialized_data):
        """Dangerous deserialization patterns"""
        results = []
        
        for data in serialized_data:
            # Pattern 1: pickle.loads
            try:
                obj = pickle.loads(data)
                results.append(obj)
            except:
                pass
            
            # Pattern 2: eval on JSON-like strings
            try:
                obj = eval(data.decode('utf-8'))
                results.append(obj)
            except:
                pass
            
            # Pattern 3: YAML unsafe loading
            try:
                obj = yaml.unsafe_load(data)
                results.append(obj)
            except:
                pass
        
        return results
    
    def weak_cryptographic_practices(self, data_list):
        """Weak crypto implementations"""
        results = []
        
        for data in data_list:
            # Pattern 1: MD5 for passwords
            md5_hash = hashlib.md5(data.encode()).hexdigest()
            results.append(md5_hash)
            
            # Pattern 2: SHA1 for security tokens
            sha1_hash = hashlib.sha1(data.encode()).hexdigest()
            results.append(sha1_hash)
            
            # Pattern 3: Base64 encoding as "encryption"
            encoded = base64.b64encode(data.encode()).decode()
            results.append(encoded)
            
            # Pattern 4: Simple XOR "encryption"
            key = 42
            encrypted = ''.join(chr(ord(c) ^ key) for c in data)
            results.append(encrypted)
        
        return results
    
    def insecure_random_generation(self):
        """Weak randomness for security purposes"""
        import random
        import time
        
        # Pattern 1: time-based seeds
        random.seed(int(time.time()))
        session_token = ''.join([str(random.randint(0, 9)) for _ in range(32)])
        
        # Pattern 2: predictable patterns
        csrf_token = f"csrf_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Pattern 3: weak password generation
        password = ''.join([chr(random.randint(65, 90)) for _ in range(8)])
        
        return {
            "session_token": session_token,
            "csrf_token": csrf_token,
            "generated_password": password
        }
    
    def xml_external_entity_vulnerabilities(self, xml_inputs):
        """XXE vulnerability patterns"""
        results = []
        
        for xml_input in xml_inputs:
            try:
                # Pattern 1: Default XML parser (vulnerable)
                root = ET.fromstring(xml_input)
                results.append(root.text)
                
                # Pattern 2: XML parser with external entities enabled
                parser = ET.XMLParser()
                root = ET.fromstring(xml_input, parser)
                results.append(root.text)
                
            except ET.ParseError as e:
                results.append(f"XML Parse Error: {e}")
        
        return results
    
    def server_side_request_forgery(self, urls):
        """SSRF vulnerability patterns"""
        results = []
        
        for url in urls:
            try:
                # Pattern 1: urllib without validation
                response = urllib.request.urlopen(url)
                results.append(response.read()[:1000])  # Limit output
                
                # Pattern 2: requests library without validation
                response = requests.get(url, timeout=5)
                results.append(response.text[:1000])
                
                # Pattern 3: Socket connections without validation
                if url.startswith('tcp://'):
                    host, port = url[6:].split(':')
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, int(port)))
                    sock.send(b"GET / HTTP/1.1\r\n\r\n")
                    data = sock.recv(1024)
                    results.append(data)
                    sock.close()
                    
            except Exception as e:
                results.append(f"Error fetching {url}: {str(e)}")
        
        return results
    
    def race_condition_vulnerabilities(self, shared_resource):
        """Race condition patterns"""
        results = []
        counter = {"value": 0}
        
        def increment_counter():
            for _ in range(1000):
                # Race condition: non-atomic increment
                temp = counter["value"]
                temp += 1
                counter["value"] = temp
                results.append(counter["value"])
        
        # Create multiple threads without proper synchronization
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return results
    
    def information_disclosure_patterns(self):
        """Information leakage vulnerabilities"""
        sensitive_info = {
            "system_info": {
                "os": os.uname(),
                "python_version": sys.version,
                "environment_variables": dict(os.environ),
                "current_directory": os.getcwd(),
                "user_info": os.getlogin() if hasattr(os, 'getlogin') else "unknown"
            },
            "database_credentials": self.config["database"],
            "api_keys": self.config["api_keys"],
            "internal_paths": [
                "/etc/passwd",
                "/proc/version", 
                "/var/log/messages",
                "/home/admin/.ssh/id_rsa"
            ],
            "debug_info": {
                "stack_trace": "".join(sys._getframe().f_back.f_locals.items()),
                "loaded_modules": list(sys.modules.keys()),
                "memory_info": sys.getsizeof(self.config)
            }
        }
        
        # Log sensitive information (vulnerability)
        self.logger.debug(f"Sensitive config loaded: {json.dumps(sensitive_info, indent=2)}")
        
        return sensitive_info
    
    def insecure_file_operations(self, file_operations):
        """Insecure file handling patterns"""
        results = []
        
        for operation in file_operations:
            try:
                if operation["type"] == "read":
                    # No path validation
                    with open(operation["filename"], 'r') as f:
                        content = f.read()
                        results.append(content)
                
                elif operation["type"] == "write":
                    # Insecure temporary files
                    temp_file = f"/tmp/{operation['filename']}"
                    with open(temp_file, 'w') as f:
                        f.write(operation["content"])
                    # Insecure permissions
                    os.chmod(temp_file, 0o777)
                    results.append(f"Written to {temp_file}")
                
                elif operation["type"] == "execute":
                    # Direct file execution
                    os.system(f"python {operation['filename']}")
                    results.append(f"Executed {operation['filename']}")
                    
            except Exception as e:
                results.append(f"File operation error: {str(e)}")
        
        return results
    
    def authentication_bypasses(self, user_credentials):
        """Authentication bypass patterns"""
        results = []
        
        for creds in user_credentials:
            # Pattern 1: Always true conditions
            if creds.get("username") == "admin" or True:
                results.append("Admin access granted")
            
            # Pattern 2: Weak password validation
            if len(creds.get("password", "")) > 0:  # Any password works
                results.append("Authentication successful")
            
            # Pattern 3: SQL injection in auth
            username = creds.get("username", "")
            if "' OR '1'='1" in username:
                results.append("SQL injection bypass successful")
            
            # Pattern 4: Hardcoded backdoor
            if creds.get("username") == "backdoor_admin_2023":
                results.append("Backdoor access granted")
        
        return results
    
    def insecure_session_management(self):
        """Session management vulnerabilities"""
        import time
        import random
        
        # Pattern 1: Predictable session IDs
        session_id_1 = f"sess_{int(time.time())}"
        
        # Pattern 2: Short random session IDs
        session_id_2 = str(random.randint(10000, 99999))
        
        # Pattern 3: Session data in URL
        session_url = f"https://app.com/dashboard?session={session_id_1}&user=admin"
        
        # Pattern 4: Session without expiration
        session_data = {
            "session_id": session_id_1,
            "user_id": "admin",
            "created_at": int(time.time()),
            "expires_at": None,  # No expiration
            "is_admin": True
        }
        
        return {
            "session_id_1": session_id_1,
            "session_id_2": session_id_2,
            "session_url": session_url,
            "session_data": session_data
        }

# Additional vulnerable functions for bulk testing
def generate_bulk_vulnerabilities(count=100):
    """Generate many vulnerable functions for performance testing"""
    vulnerable_functions = {}
    
    for i in range(count):
        # Command injection variants
        exec(f"""
def vuln_cmd_injection_{i}(user_input):
    return os.system(f"echo {{user_input}}")
""")
        
        # SQL injection variants  
        exec(f"""
def vuln_sql_injection_{i}(user_id):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    query = f"SELECT * FROM table_{i} WHERE id = {{user_id}}"
    cursor.execute(query)
    return cursor.fetchall()
""")
        
        # Hardcoded secret variants
        exec(f"""
def hardcoded_secret_{i}():
    secret = "hardcoded_secret_key_{i}_2023"
    api_key = "sk-{i}_secret_api_key_production"
    return secret, api_key
""")
    
    return vulnerable_functions

# Generate bulk test cases
bulk_vulns = generate_bulk_vulnerabilities(200)

# Large data structures with embedded vulnerabilities
LARGE_CONFIG = {
    f"service_{i}": {
        "api_key": f"sk-prod-{i}_{''.join([str(j) for j in range(20)])}",
        "secret": f"secret_key_service_{i}_production_2023",
        "database_url": f"postgresql://admin:password123@db-{i}.internal.com:5432/app_{i}",
        "redis_url": f"redis://admin:redis_pwd_123@cache-{i}.internal.com:6379/0",
        "smtp_credentials": {
            "username": f"service-{i}@company.com",
            "password": f"smtp_password_service_{i}_2023"
        },
        "encryption_keys": [
            f"AES_KEY_{i}_{''.join([str(j) for j in range(32)])}",
            f"RSA_PRIVATE_KEY_{i}_BEGIN_PRIVATE_KEY_DATA_HERE",
            f"JWT_SECRET_{i}_{''.join([str(j) for j in range(64)])}"
        ]
    }
    for i in range(500)  # Large configuration with many services
}

# Performance testing utilities
class SecurityPerformanceTests:
    """Performance testing for security scanning"""
    
    def __init__(self):
        self.test_cases = []
        
    def generate_test_cases(self, size_categories):
        """Generate test cases of various sizes"""
        for category, size in size_categories.items():
            test_case = self._create_test_case(size)
            self.test_cases.append({
                "category": category,
                "size": len(test_case),
                "content": test_case
            })
    
    def _create_test_case(self, target_size):
        """Create a test case of approximately target size"""
        base_vulnerabilities = [
            'os.system(user_input)',
            'eval(user_code)', 
            'pickle.loads(data)',
            'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
            'password = "hardcoded_password_123"',
            'api_key = "sk-1234567890abcdef"',
            'hashlib.md5(password.encode()).hexdigest()',
            'urllib.request.urlopen(user_url)',
            'subprocess.run(command, shell=True)',
            'with open(f"/tmp/{filename}", "w") as f:'
        ]
        
        content = "# Performance test case\n"
        while len(content) < target_size:
            for vuln in base_vulnerabilities:
                content += f"def test_func_{len(content)}():\n"
                content += f"    {vuln}\n"
                content += "    return 'test'\n\n"
                if len(content) >= target_size:
                    break
        
        return content[:target_size]

# Initialize performance test suite
perf_tester = SecurityPerformanceTests()
perf_tester.generate_test_cases({
    "tiny": 1024,      # 1KB
    "small": 10240,    # 10KB  
    "medium": 102400,  # 100KB
    "large": 1048576   # 1MB
})

# Export test data for benchmarking
TEST_DATA_EXPORT = {
    "config": LARGE_CONFIG,
    "bulk_vulnerabilities": bulk_vulns,
    "performance_test_cases": perf_tester.test_cases,
    "comprehensive_suite": ComprehensiveSecurityTestSuite()
}

if __name__ == "__main__":
    # Performance testing entry point
    suite = ComprehensiveSecurityTestSuite()
    
    # Run comprehensive tests
    print("Starting comprehensive security vulnerability testing...")
    
    test_results = {
        "command_injection": suite.command_injection_vulnerabilities(["test", "admin", "../../etc/passwd"]),
        "sql_injection": suite.sql_injection_vulnerabilities([
            {"username": "admin", "email": "test@test.com", "user_id": "1"},
            {"username": "' OR '1'='1", "email": "hack@test.com", "user_id": "2"}
        ]),
        "information_disclosure": suite.information_disclosure_patterns(),
        "weak_crypto": suite.weak_cryptographic_practices(["password123", "secret_token"]),
        "insecure_random": suite.insecure_random_generation(),
        "session_management": suite.insecure_session_management()
    }
    
    print(f"Test execution completed. Results contain {len(str(test_results))} characters of output.")
    print("This code contains intentional security vulnerabilities for testing purposes.")