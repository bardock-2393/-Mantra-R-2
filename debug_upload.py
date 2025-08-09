#!/usr/bin/env python3
"""
Debug Upload System - Test streaming upload endpoints
"""

import requests
import json
import time

def test_server_connection():
    """Test if server is running"""
    print("🔍 Testing server connection...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running on port 8000")
            return True
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server on port 8000")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_upload_init():
    """Test upload initialization endpoint"""
    print("\n🧪 Testing upload initialization...")
    
    test_data = {
        "filename": "test_video.mp4",
        "size": 1073741824  # 1GB
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/upload/init",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data),
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload init successful:")
            print(f"   Upload ID: {result.get('upload_id', 'N/A')}")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            print(f"   Chunk Size: {result.get('chunk_size', 'N/A')}")
            return result.get('upload_id')
        else:
            print(f"❌ Upload init failed:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload init error: {e}")
        return None

def test_analysis_types():
    """Test analysis types endpoint"""
    print("\n🧪 Testing analysis types endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/api/analysis-types", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis types available: {len(result.get('analysis_types', []))}")
            return True
        else:
            print(f"❌ Analysis types failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis types error: {e}")
        return False

def test_nginx_proxy():
    """Test nginx proxy"""
    print("\n🧪 Testing nginx proxy...")
    
    try:
        # Test direct connection
        direct_response = requests.get("http://localhost:8000/", timeout=5)
        print(f"📡 Direct (port 8000): {direct_response.status_code}")
        
        # Test proxy connection
        proxy_response = requests.get("http://localhost/", timeout=5)
        print(f"🔄 Proxy (port 80): {proxy_response.status_code}")
        
        if direct_response.status_code == 200 and proxy_response.status_code == 200:
            print("✅ Both direct and proxy connections work")
            return True
        else:
            print("⚠️ Some connections failed")
            return False
            
    except Exception as e:
        print(f"❌ Proxy test error: {e}")
        return False

def main():
    """Run all debug tests"""
    print("🔧 AI Video Detective - Upload Debug Tool")
    print("=" * 50)
    
    # Test server connection
    if not test_server_connection():
        print("\n💡 To start the server, run:")
        print("   python start_app.py")
        print("   # or")
        print("   python app.py")
        return
    
    # Test upload endpoints
    upload_id = test_upload_init()
    
    # Test other endpoints
    test_analysis_types()
    
    # Test nginx proxy
    test_nginx_proxy()
    
    print("\n📊 Debug Summary:")
    print(f"   Server: {'✅ Running' if test_server_connection() else '❌ Down'}")
    print(f"   Upload Init: {'✅ Working' if upload_id else '❌ Failed'}")
    print(f"   Analysis Types: {'✅ Working' if test_analysis_types() else '❌ Failed'}")
    
    if upload_id:
        print(f"\n🎯 Upload system appears to be working!")
        print(f"   You can now test with a real file upload")
    else:
        print(f"\n⚠️ Upload system has issues - check server logs")

if __name__ == "__main__":
    main()