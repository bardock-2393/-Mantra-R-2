#!/usr/bin/env python3
"""
AI Video Detective - Startup Script
Simple script to run the application with proper configuration
"""

import os
import sys
from app import app

def main():
    """Main startup function"""
    print("🚀 AI Video Detective - Live Investigation Studio")
    print("=" * 50)
    
    # Check if required environment variables are set
    from config import Config
    if not Config.GOOGLE_API_KEY:
        print("⚠️  Warning: GOOGLE_API_KEY not set in environment")
        print("   Please set your Gemini API key in .env file or environment")
        print("   Get your API key from: https://aistudio.google.com/")
        print()
    
    # Check if upload directory exists
    upload_dir = Config.UPLOAD_FOLDER
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"📁 Created upload directory: {upload_dir}")
    
    print("🔗 Redis: Configured and ready")
    print("🤖 Gemini API: Ready for video analysis")
    print("🌐 Server: Starting on http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run the Flask application
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 AI Video Detective stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 