"""
AI Video Detective - Main Application
Advanced AI video analysis application with comprehensive understanding capabilities
"""

import os
import threading
import time
from flask import Flask
from config import Config
from routes.main_routes import main_bp
from routes.chat_routes import chat_bp
from routes.api_routes import api_bp
from services.session_service import cleanup_expired_sessions, cleanup_old_uploads
from services.ai_service import initialize_model

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure Flask
    app.secret_key = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp)
    
    return app

def start_cleanup_thread():
    """Start background cleanup thread"""
    def periodic_cleanup():
        while True:
            time.sleep(1800)  # 30 minutes
            print("🧹 Running periodic cleanup...")
            cleanup_expired_sessions()
            cleanup_old_uploads()
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    return cleanup_thread

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Clean up expired sessions on startup
    print("🧹 Cleaning up expired sessions...")
    cleanup_expired_sessions()
    
    # Start background cleanup thread
    cleanup_thread = start_cleanup_thread()
    
    print("🚀 AI Video Detective Starting...")
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🔗 Redis URL: {Config.REDIS_URL}")
    print(f"🤖 AI Model: Gemma 3 (Local Processing)")
    
    # Initialize model once at startup - MASSIVE SPEED BOOST!
    import time
    model_start = time.time()
    print("🤖 Initializing Gemma 3 model...")
    initialize_model()
    model_time = time.time() - model_start
    print(f"✅ Model ready for real-time analysis! (loaded in {model_time:.2f}s)")
    
    app.run(host='0.0.0.0', port=8000, debug=True) 