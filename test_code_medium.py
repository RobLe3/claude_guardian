# Medium test code sample (10KB)
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

class SecurityTestClass:
    def __init__(self):
        # Multiple security vulnerabilities for testing
        self.api_key = "sk-1234567890abcdef"  # Hardcoded API key
        self.database_password = "admin123"   # Weak password
        self.secret_token = "super_secret_token_2023"
        
    def command_injection_vuln(self, user_input):
        """Command injection vulnerability"""
        command = f"ls {user_input}"
        result = os.system(command)  # Vulnerable to command injection
        return result
    
    def sql_injection_vuln(self, user_id):
        """SQL injection vulnerability"""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        # Vulnerable SQL query
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)  # SQL injection risk
        return cursor.fetchall()
    
    def path_traversal_vuln(self, filename):
        """Path traversal vulnerability"""
        # No input validation - path traversal risk
        with open(f"/var/logs/{filename}", 'r') as f:
            return f.read()
    
    def deserialization_vuln(self, data):
        """Insecure deserialization"""
        # Dangerous pickle usage
        return pickle.loads(data)  # Insecure deserialization
    
    def weak_crypto(self, data):
        """Weak cryptographic practices"""
        # Using MD5 for security purposes (weak)
        return hashlib.md5(data.encode()).hexdigest()
    
    def insecure_random(self):
        """Insecure random number generation"""
        import random
        # Using weak random for security tokens
        return random.randint(1000, 9999)  # Weak randomness
    
    def url_injection(self, user_url):
        """URL injection vulnerability"""
        # No URL validation
        response = urllib.request.urlopen(user_url)  # SSRF risk
        return response.read()
    
    def file_upload_vuln(self, uploaded_file):
        """Insecure file upload"""
        # No file type validation
        with open(f"/tmp/{uploaded_file.name}", 'wb') as f:
            f.write(uploaded_file.read())
        # Execute uploaded file without validation
        os.system(f"python /tmp/{uploaded_file.name}")  # RCE risk
    
    def debug_info_leak(self, error):
        """Information disclosure through error messages"""
        # Exposing stack traces and system info
        import traceback
        return {
            "error": str(error),
            "traceback": traceback.format_exc(),
            "system_info": os.uname(),
            "environment": dict(os.environ)  # Environment leak
        }
    
    def insecure_session(self):
        """Insecure session management"""
        # Predictable session IDs
        import time
        session_id = f"sess_{int(time.time())}"  # Predictable
        return session_id
    
    def credential_storage(self):
        """Insecure credential storage"""
        credentials = {
            "username": "admin",
            "password": "password123",  # Plain text storage
            "admin_token": "admin_secret_2023",
            "database_url": "postgresql://admin:password@localhost:5432/db"
        }
        return credentials

# Additional vulnerable patterns
def eval_injection(user_code):
    """Code injection through eval"""
    return eval(user_code)  # Dangerous eval usage

def format_string_vuln(user_input):
    """Format string vulnerability"""
    return f"User input: {user_input}".format()  # Potential format string issue

# Simulate a larger codebase with repetitive patterns
for i in range(50):
    globals()[f'vuln_function_{i}'] = lambda x: os.system(f"echo {x}")

# More test patterns
HARDCODED_SECRETS = [
    "password123",
    "secret_key_2023", 
    "api_token_xyz789",
    "database_admin_pwd"
]

def process_user_data(data):
    """Multiple vulnerabilities in one function"""
    # XSS vulnerability
    html_output = f"<div>User data: {data}</div>"  # No escaping
    
    # Command injection
    os.system(f"echo '{data}' >> /tmp/user_data.log")
    
    # Insecure temp file
    temp_file = f"/tmp/user_data_{data}"
    with open(temp_file, 'w') as f:
        f.write(data)
    
    return html_output