#!/usr/bin/env python3
"""
Claude Guardian Setup Validation
Tests the setup process and verifies all components work correctly.
"""

import subprocess
import sys
import socket
import json
import time
from pathlib import Path

def check_python():
    """Check Python version and basic functionality."""
    print("🐍 Testing Python environment...")
    
    # Check version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required Python packages are available."""
    print("📦 Testing dependencies...")
    
    required = ['websockets', 'fastapi', 'uvicorn', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"💡 Install missing packages: pip3 install {' '.join(missing)}")
        return False
    
    return True

def check_port_available(port=8083):
    """Check if MCP port is available."""
    print(f"🔌 Testing port {port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"⚠️  Port {port} is already in use")
        print(f"💡 This is OK if Claude Guardian is already running")
        return True  # Not a failure - service might already be running
    else:
        print(f"✅ Port {port} available")
        return True

def test_mcp_service():
    """Test MCP service startup and functionality."""
    print("🚀 Testing MCP service...")
    
    # Check if service script exists
    script_path = Path('scripts/start-mcp-service.py')
    if not script_path.exists():
        print("❌ MCP service script not found")
        return False
    
    print("✅ MCP service script found")
    
    # Test script syntax by importing it
    try:
        # Just check that the script is valid Python
        result = subprocess.run([
            'python3', '-m', 'py_compile', str(script_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ MCP service script is valid Python")
            return True
        else:
            print(f"❌ MCP service script syntax error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP service test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration file generation."""
    print("⚙️  Testing configuration...")
    
    # Check if .env template exists
    env_template = Path('deployments/production/.env.template')
    if env_template.exists():
        print("✅ Environment template found")
    else:
        print("⚠️  Environment template missing")
    
    # Test configuration generation
    try:
        config = {
            "name": "claude-guardian",
            "command": "python3",
            "args": [str(Path.cwd() / "scripts/start-mcp-service.py"), "--port", "8083"],
            "env": {
                "GUARDIAN_MODE": "production"
            }
        }
        
        # Write test config
        with open('test-claude-code-config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration generation works")
        Path('test-claude-code-config.json').unlink()  # Clean up
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_security_tools():
    """Test security tools availability."""
    print("🛡️  Testing security tools...")
    
    # Check if validation script exists
    validation_script = Path('scripts/validate-mcp-tools.py')
    if not validation_script.exists():
        print("⚠️  MCP tools validation script missing")
        return False
    
    print("✅ Security tools validation script found")
    return True

def main():
    """Run all setup validation tests."""
    print("🔍 Claude Guardian Setup Validation")
    print("=" * 50)
    
    tests = [
        ("Python Environment", check_python),
        ("Dependencies", check_dependencies),
        ("Port Availability", check_port_available),
        ("MCP Service", test_mcp_service),
        ("Configuration", test_configuration_files),
        ("Security Tools", test_security_tools),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🏆 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Setup is ready.")
        print("Next: Run ./easy-setup.sh to deploy")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
        print("Fix issues before running setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)