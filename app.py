"""
AI Video Detective - Main Application with Real-time WebSocket Support
Advanced AI video analysis application with lightning-fast real-time communication
"""

import os
import threading
import time
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import Config
from routes.main_routes import main_bp
from routes.chat_routes import chat_bp
from routes.api_routes import api_bp
from services.session_service import cleanup_expired_sessions, cleanup_old_uploads
from services.ai_service import initialize_model
from services.websocket_service import initialize_websocket_service

def create_app():
    """Create and configure the Flask application with SocketIO for real-time communication"""
    app = Flask(__name__)
    
    # Configure Flask
    app.secret_key = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # Initialize SocketIO for lightning-fast real-time communication
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',  # Compatible async mode for Python 3.13
        logger=True,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25
    )
    
    # Initialize WebSocket service
    initialize_websocket_service(socketio)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp)
    
    # WebSocket event handlers for real-time communication
    @socketio.on('connect')
    def handle_connect():
        print('🔗 Client connected to WebSocket for real-time updates')
        emit('connected', {
            'message': '🚀 Real-time connection established - Ready for lightning-fast analysis!',
            'timestamp': time.time()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('🔌 Client disconnected from WebSocket')
    
    @socketio.on('join_session')
    def handle_join_session(data):
        session_id = data.get('session_id')
        if session_id:
            join_room(session_id)
            print(f'📡 Client joined session: {session_id} for real-time updates')
            emit('session_joined', {
                'session_id': session_id,
                'message': f'🎯 Joined session for real-time video analysis updates',
                'timestamp': time.time()
            })
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        session_id = data.get('session_id')
        if session_id:
            leave_room(session_id)
            print(f'📡 Client left session: {session_id}')
    
    @socketio.on('ping')
    def handle_ping():
        emit('pong', {'timestamp': time.time()})
    
    return app, socketio

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

# Create the application instance with SocketIO
app, socketio = create_app()

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Clean up expired sessions on startup
    print("🧹 Cleaning up expired sessions...")
    cleanup_expired_sessions()
    
    # Start background cleanup thread
    cleanup_thread = start_cleanup_thread()
    
    print("🚀 AI Video Detective Starting with Real-time WebSocket Support...")
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🔗 Redis URL: {Config.REDIS_URL}")
    print(f"🤖 AI Model: Gemma 3 (Local Processing)")
    print(f"⚡ WebSocket: Real-time communication enabled for lightning-fast analysis!")
    
    # Initialize model once at startup - MASSIVE SPEED BOOST!
    model_start = time.time()
    print("🤖 Initializing Gemma 3 model...")
    initialize_model()
    model_time = time.time() - model_start
    print(f"✅ Model ready for real-time analysis! (loaded in {model_time:.2f}s)")
    
    # Run with SocketIO for real-time support
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=True,
        use_reloader=False  # Disable reloader to prevent model reloading
    ) 