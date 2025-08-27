# Small test code sample (1KB)
import os
import subprocess

def vulnerable_function():
    user_input = input("Enter command: ")
    # Security vulnerability: Command injection
    os.system(user_input)
    
    password = "hardcoded_password_123"
    
    return "Executed"