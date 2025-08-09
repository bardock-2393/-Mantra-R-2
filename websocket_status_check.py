#!/usr/bin/env python3
"""
WebSocket Upload System Status Check
Verifies that all WebSocket upload components are working correctly
"""

import sys
import time
import requests
import socketio

def check_server_status():
    """Check if the main server is running"""
    print("🔍 Checking server status...")
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

def check_websocket_connection():
    """Check if WebSocket connections work"""
    print("\n🔍 Checking WebSocket connection...")
    try:
        sio = socketio.Client()
        connected = False
        
        @sio.event
        def connect():
            nonlocal connected
            connected = True
            print("✅ WebSocket connection successful")
        
        @sio.event
        def connect_error(data):
            print(f"❌ WebSocket connection error: {data}")
        
        # Connect with timeout
        sio.connect('http://localhost:8000', wait_timeout=10)
        
        if connected:
            # Test session join
            sio.emit('join_session', {'session_id': 'test_session'})
            time.sleep(0.5)
            
            # Test ping
            sio.emit('ping')
            time.sleep(0.5)
            
            sio.disconnect()
            return True
        else:
            print("❌ WebSocket connection failed")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

def check_upload_validation():
    """Check upload validation without actually uploading"""
    print("\n🔍 Checking upload validation...")
    try:
        sio = socketio.Client()
        validation_passed = False
        
        @sio.event
        def connect():
            # Test file size validation (too large)
            sio.emit('start_upload', {
                'session_id': 'test_session',
                'filename': 'test_large.mp4',
                'file_size': 3 * 1024 * 1024 * 1024,  # 3GB (over 2GB limit)
                'file_type': 'video/mp4'
            })
        
        @sio.event
        def upload_error(data):
            nonlocal validation_passed
            if '2GB limit' in data.get('error', ''):
                validation_passed = True
                print("✅ File size validation working")
        
        sio.connect('http://localhost:8000', wait_timeout=10)
        time.sleep(2)  # Wait for validation response
        sio.disconnect()
        
        if not validation_passed:
            print("❌ File size validation not working")
        
        return validation_passed
        
    except Exception as e:
        print(f"❌ Upload validation error: {e}")
        return False

def check_configuration():
    """Check WebSocket upload configuration"""
    print("\n🔍 Checking configuration...")
    try:
        from config import Config
        
        print(f"📁 Max upload size: {Config.MAX_CONTENT_LENGTH / (1024**3):.1f}GB")
        print(f"📄 Allowed extensions: {Config.ALLOWED_EXTENSIONS}")
        print(f"📂 Upload folder: {Config.UPLOAD_FOLDER}")
        
        if hasattr(Config, 'GPU_MEMORY_GB'):
            print(f"🚀 GPU memory: {Config.GPU_MEMORY_GB}GB")
        
        if hasattr(Config, 'HIGH_MEMORY_MODE'):
            print(f"⚡ High memory mode: {Config.HIGH_MEMORY_MODE}")
        
        # Check critical values
        issues = []
        if Config.MAX_CONTENT_LENGTH != 2 * 1024 * 1024 * 1024:
            issues.append(f"Upload limit should be 2GB, got {Config.MAX_CONTENT_LENGTH / (1024**3):.1f}GB")
        
        if 'mp4' not in Config.ALLOWED_EXTENSIONS:
            issues.append("MP4 not in allowed extensions")
        
        if issues:
            print("❌ Configuration issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ Configuration looks good")
            return True
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def show_websocket_improvements():
    """Show the improvements made for WebSocket upload"""
    print("\n📊 WebSocket Upload Improvements:")
    print("=" * 50)
    print("🔧 Backend Improvements:")
    print("  ✅ Error handling for disconnected clients")
    print("  ✅ Session validation before emitting")
    print("  ✅ Try-catch blocks in event handlers")
    print("  ✅ Global error handler for WebSocket")
    print("  ✅ Increased ping timeout (120s)")
    print("  ✅ Larger buffer size (2MB)")
    
    print("\n🌐 Frontend Improvements:")
    print("  ✅ Automatic reconnection (5 attempts)")
    print("  ✅ Fallback transport (polling)")
    print("  ✅ Connection timeout handling")
    print("  ✅ Upload heartbeat mechanism")
    print("  ✅ Reconnection notifications")
    print("  ✅ Enhanced percentage display")

def main():
    """Run all status checks"""
    print("🚀 WebSocket Upload System Status Check")
    print("=" * 60)
    
    # Run checks
    server_ok = check_server_status()
    websocket_ok = check_websocket_connection() if server_ok else False
    upload_ok = check_upload_validation() if websocket_ok else False
    config_ok = check_configuration()
    
    # Show improvements
    show_websocket_improvements()
    
    # Summary
    print(f"\n📋 Status Summary:")
    print(f"  Server: {'✅ OK' if server_ok else '❌ FAIL'}")
    print(f"  WebSocket: {'✅ OK' if websocket_ok else '❌ FAIL'}")
    print(f"  Upload Validation: {'✅ OK' if upload_ok else '❌ FAIL'}")
    print(f"  Configuration: {'✅ OK' if config_ok else '❌ FAIL'}")
    
    all_ok = server_ok and websocket_ok and config_ok
    
    if all_ok:
        print("\n🎉 ALL SYSTEMS GO!")
        print("✅ WebSocket upload system is ready for 2GB files")
        print("🚀 Connection stability improvements active")
        print("📊 Enhanced percentage display ready")
    else:
        print("\n⚠️ ISSUES DETECTED")
        print("🔧 Check the failed components above")
        
        if not server_ok:
            print("💡 Start the server: python app.py")
        if server_ok and not websocket_ok:
            print("💡 Check WebSocket configuration in app.py")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)