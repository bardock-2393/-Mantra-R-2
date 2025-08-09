#!/usr/bin/env python3
"""
AI Video Detective - Production Startup Script
Ensures proper initialization and error handling
"""

import os
import sys
import time
from config import Config

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch not found")
        return False
    
    try:
        from transformers import AutoProcessor, PaliGemmaForConditionalGeneration
        print("✅ Transformers library available")
    except ImportError:
        print("❌ Transformers library not found")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV not found")
        return False
    
    return True

def setup_environment():
    """Setup upload folders and environment"""
    print("🔧 Setting up environment...")
    
    # Create upload folder
    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    print(f"📂 Upload folder: {upload_folder}")
    
    # Create logs folder
    logs_folder = "logs"
    os.makedirs(logs_folder, exist_ok=True)
    print(f"📋 Logs folder: {logs_folder}")
    
    # Check disk space
    statvfs = os.statvfs('.')
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    free_gb = free_bytes / (1024**3)
    print(f"💾 Free disk space: {free_gb:.1f}GB")
    
    if free_gb < 5:
        print("⚠️ Warning: Low disk space (< 5GB)")
    
    return True

def start_application():
    """Start the Flask application"""
    print("🚀 Starting AI Video Detective...")
    print(f"🌐 Server will run on: http://0.0.0.0:8000")
    print(f"📊 Max upload size: {Config.MAX_CONTENT_LENGTH / (1024**3):.1f}GB")
    print(f"🔥 GPU optimized: {getattr(Config, 'HIGH_MEMORY_MODE', False)}")
    print()
    
    # Import and run the app
    from app import create_app, socketio
    
    app = create_app()
    
    # Initialize model
    from services.ai_service import initialize_model
    print("🤖 Initializing AI model...")
    start_time = time.time()
    initialize_model()
    init_time = time.time() - start_time
    print(f"✅ AI model ready! (loaded in {init_time:.2f}s)")
    
    # Start the server
    print("🎯 Server starting...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=False,  # Set to False for production
        use_reloader=False
    )

def main():
    """Main startup function"""
    print("=" * 60)
    print("🎬 AI Video Detective - Production Server")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependencies check failed")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Start application
    try:
        start_application()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()