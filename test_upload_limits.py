#!/usr/bin/env python3
"""
Upload Limit Configuration Test
Verifies that all upload limits are properly set to 2GB
"""

import os
import re
from config import Config

def test_backend_config():
    """Test backend configuration"""
    print("🔧 Testing Backend Configuration:")
    
    # Check Flask config
    max_content_gb = Config.MAX_CONTENT_LENGTH / (1024**3)
    print(f"  ✅ MAX_CONTENT_LENGTH: {max_content_gb:.1f}GB")
    
    if max_content_gb == 2.0:
        print("  ✅ Backend limit correctly set to 2GB")
        return True
    else:
        print(f"  ❌ Expected 2GB, got {max_content_gb:.1f}GB")
        return False

def test_frontend_config():
    """Test frontend JavaScript configuration"""
    print("\n🌐 Testing Frontend Configuration:")
    
    try:
        with open('static/js/app.js', 'r') as f:
            content = f.read()
        
        # Look for file size check
        size_check = re.search(r'file\.size > (\d+) \* 1024 \* 1024 \* 1024', content)
        if size_check:
            size_gb = int(size_check.group(1))
            print(f"  ✅ JavaScript file size limit: {size_gb}GB")
            
            if size_gb == 2:
                print("  ✅ Frontend limit correctly set to 2GB")
                return True
            else:
                print(f"  ❌ Expected 2GB, got {size_gb}GB")
                return False
        else:
            print("  ❌ Could not find file size check in JavaScript")
            return False
            
    except FileNotFoundError:
        print("  ❌ JavaScript file not found")
        return False

def test_html_template():
    """Test HTML template display"""
    print("\n📄 Testing HTML Template:")
    
    try:
        with open('templates/index.html', 'r') as f:
            content = f.read()
        
        if "Maximum size: 2GB" in content:
            print("  ✅ HTML template shows 2GB limit")
            return True
        elif "Maximum size: 100MB" in content:
            print("  ❌ HTML template still shows old 100MB limit")
            return False
        else:
            print("  ⚠️ Could not find size limit in HTML template")
            return False
            
    except FileNotFoundError:
        print("  ❌ HTML template not found")
        return False

def test_readme_documentation():
    """Test README documentation"""
    print("\n📚 Testing README Documentation:")
    
    try:
        with open('README.md', 'r') as f:
            content = f.read()
        
        if "2GB" in content and "80GB GPU optimized" in content:
            print("  ✅ README updated with 2GB limit and GPU optimization notes")
            return True
        elif "100MB" in content:
            print("  ⚠️ README may still contain old 100MB references")
            return False
        else:
            print("  ⚠️ Could not verify README upload limits")
            return False
            
    except FileNotFoundError:
        print("  ❌ README file not found")
        return False

def show_upload_summary():
    """Show upload configuration summary"""
    print("\n📊 Upload Configuration Summary:")
    print("=" * 50)
    print(f"🔧 Backend Limit: {Config.MAX_CONTENT_LENGTH / (1024**3):.1f}GB")
    print(f"🎯 Target: 2GB (80GB GPU optimized)")
    print(f"📁 Supported Formats: {', '.join(Config.ALLOWED_EXTENSIONS)}")
    print(f"🚀 GPU Memory: {getattr(Config, 'GPU_MEMORY_GB', 'Not specified')}GB")
    print(f"⚡ High Memory Mode: {getattr(Config, 'HIGH_MEMORY_MODE', False)}")

def main():
    """Run all upload limit tests"""
    print("🚀 Upload Limit Configuration Test")
    print("=" * 50)
    
    backend_ok = test_backend_config()
    frontend_ok = test_frontend_config()
    html_ok = test_html_template()
    readme_ok = test_readme_documentation()
    
    show_upload_summary()
    
    # Final result
    all_ok = backend_ok and frontend_ok and html_ok and readme_ok
    
    print(f"\n📋 Test Results:")
    print(f"  Backend Config: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"  Frontend JS: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"  HTML Template: {'✅ PASS' if html_ok else '❌ FAIL'}")
    print(f"  README Docs: {'✅ PASS' if readme_ok else '❌ FAIL'}")
    
    if all_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Upload limit successfully configured to 2GB")
        print("🚀 System ready for 80GB GPU optimized uploads")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Check the failed components and fix configuration")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)