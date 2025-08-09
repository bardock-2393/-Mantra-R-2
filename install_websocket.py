#!/usr/bin/env python3
"""
WebSocket Installation Script for AI Video Detective
Installs Flask-SocketIO and related dependencies for real-time communication
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main installation function"""
    print("🚀 AI Video Detective - WebSocket Real-time Communication Setup")
    print("=" * 70)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  WARNING: Not in a virtual environment. It's recommended to use one.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
    
    # Install WebSocket dependencies
    websocket_packages = [
        "flask-socketio==5.3.7",
        "python-socketio==5.11.4", 
        "python-engineio==4.10.1",
        "eventlet==0.36.1"
    ]
    
    print(f"\n📦 Installing WebSocket packages:")
    for package in websocket_packages:
        print(f"   - {package}")
    
    # Install packages
    for package in websocket_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"❌ Failed to install {package}")
            return False
    
    print("\n🔧 Installing from requirements.txt (includes WebSocket support)...")
    if not run_command("pip install -r requirements.txt", "Installing all requirements"):
        print("❌ Failed to install requirements")
        return False
    
    print("\n🧪 Testing WebSocket installation...")
    test_script = '''
import flask_socketio
import socketio
import eventlet
print("✅ Flask-SocketIO:", flask_socketio.__version__)
print("✅ Socket.IO:", socketio.__version__)
print("✅ Eventlet:", eventlet.__version__)
print("🚀 All WebSocket dependencies installed successfully!")
'''
    
    try:
        exec(test_script)
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 WebSocket Real-time Communication Setup Complete!")
    print("\n📋 What's New:")
    print("   ✅ Real-time progress updates during video analysis")
    print("   ✅ Live frame extraction feedback for long videos")
    print("   ✅ Instant AI thinking indicators")
    print("   ✅ Real-time chat responses")
    print("   ✅ WebSocket-based error notifications")
    print("   ✅ Smart sampling notifications for 120+ minute videos")
    
    print("\n🚀 To start the application with real-time features:")
    print("   python app.py")
    
    print("\n💡 Features:")
    print("   - Lightning-fast real-time updates")
    print("   - Perfect for 120-minute videos at 720p/90fps")
    print("   - A100 GPU optimized with WebSocket streaming")
    print("   - No more waiting - see progress instantly!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)