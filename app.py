"""
AI Video Detective - Main Flask Application
Distributed Architecture with Local Development Environment and Remote GPU Server
"""

import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import redis
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from services.ai_service import AIService
from services.session_service import SessionService
from services.video_service import VideoService
from services.audio_service import AudioService
from services.event_service import EventService
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

class AIVideoDetectiveApp:
    """Main Flask application for AI Video Detective"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ai-video-detective-secret-key')
        self.app.config['MAX_CONTENT_LENGTH'] = config.network.max_file_size
        
        # Initialize services
        self._init_services()
        
        # Setup Flask extensions
        self._setup_extensions()
        
        # Register routes
        self._register_routes()
        
        # Setup error handlers
        self._setup_error_handlers()
    
    def _init_services(self):
        """Initialize all services"""
        try:
            # Redis connection
            redis_config = config.get_redis_config()
            self.redis_client = redis.Redis(**redis_config)
            
            # Core services
            self.session_service = SessionService(self.redis_client)
            self.video_service = VideoService(config)
            self.audio_service = AudioService(config)
            self.event_service = EventService(config)
            
            # AI service (only on remote server)
            if config.is_remote_server:
                self.ai_service = AIService(config)
            else:
                self.ai_service = None
                
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _setup_extensions(self):
        """Setup Flask extensions"""
        # CORS
        CORS(self.app, origins=config.security.cors_origins)
        
        # SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=config.security.cors_origins,
            ping_timeout=config.network.websocket_ping_timeout,
            ping_interval=config.network.websocket_ping_interval,
            async_mode='threading'  # Use threading instead of gevent for better compatibility
        )
        
        # Setup SocketIO events
        self._setup_socketio_events()
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            session_id = request.args.get('session')
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Create or get session
            session = self.session_service.create_session(session_id)
            
            logger.info(f"Client connected: {session_id}")
            emit('connected', {'session_id': session_id, 'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            session_id = request.args.get('session')
            if session_id:
                self.session_service.cleanup_session(session_id)
                logger.info(f"Client disconnected: {session_id}")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat messages"""
            try:
                session_id = data.get('session_id')
                message = data.get('message')
                video_id = data.get('video_id')
                
                if not session_id or not message:
                    emit('error', {'message': 'Missing session_id or message'})
                    return
                
                # Process message based on environment
                if config.is_remote_server:
                    # Remote server: process directly
                    response = self._process_chat_message_remote(session_id, message, video_id)
                else:
                    # Local server: forward to remote
                    response = self._process_chat_message_local(session_id, message, video_id)
                
                emit('chat_response', response)
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                emit('error', {'message': f'Error processing message: {str(e)}'})
        
        @self.socketio.on('upload_progress')
        def handle_upload_progress(data):
            """Handle upload progress updates"""
            video_id = data.get('video_id')
            progress = data.get('progress')
            
            if video_id and progress is not None:
                # Publish progress to Redis
                self.redis_client.publish(f'progress:{video_id}', json.dumps({
                    'progress': progress,
                    'timestamp': datetime.now().isoformat()
                }))
    
    def _process_chat_message_remote(self, session_id: str, message: str, video_id: str = None):
        """Process chat message on remote server"""
        if not self.ai_service:
            return {'error': 'AI service not available'}
        
        try:
            # Get session context
            session = self.session_service.get_session(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            # Process with AI service
            response = self.ai_service.process_query(
                message=message,
                video_id=video_id,
                session_context=session.get('context', [])
            )
            
            # Update session context
            session['context'].append({
                'user': message,
                'assistant': response.get('answer', ''),
                'timestamp': datetime.now().isoformat()
            })
            self.session_service.update_session(session_id, session)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in remote chat processing: {e}")
            return {'error': f'Processing error: {str(e)}'}
    
    def _process_chat_message_local(self, session_id: str, message: str, video_id: str = None):
        """Process chat message on local server (forward to remote)"""
        try:
            # Forward to remote GPU server
            import requests
            
            remote_url = f"{config.remote_gpu_server_url}/api/chat"
            payload = {
                'session_id': session_id,
                'message': message,
                'video_id': video_id
            }
            
            response = requests.post(remote_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error forwarding to remote server: {e}")
            return {'error': f'Remote server error: {str(e)}'}
    
    def _register_routes(self):
        """Register Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return send_from_directory('templates', 'index.html')
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'environment': config.env,
                'is_remote_server': config.is_remote_server
            })
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_video():
            """Upload video file"""
            try:
                if 'video' not in request.files:
                    return jsonify({'error': 'No video file provided'}), 400
                
                video_file = request.files['video']
                if video_file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                # Validate file format
                file_ext = Path(video_file.filename).suffix.lower()
                if file_ext not in config.storage.supported_video_formats:
                    return jsonify({'error': f'Unsupported format: {file_ext}'}), 400
                
                # Generate video ID
                video_id = str(uuid.uuid4())
                
                # Save file
                filename = f"{video_id}_{video_file.filename}"
                filepath = os.path.join(config.storage.local_upload_dir, filename)
                video_file.save(filepath)
                
                # Process video based on environment
                if config.is_remote_server:
                    # Remote server: process directly
                    result = self._process_video_remote(video_id, filepath)
                else:
                    # Local server: process locally instead of forwarding
                    result = self._process_video_local(video_id, filepath)
                
                return jsonify({
                    'video_id': video_id,
                    'filename': filename,
                    'status': 'uploaded',
                    'processing': result
                })
                
            except Exception as e:
                logger.error(f"Error uploading video: {e}")
                return jsonify({'error': f'Upload error: {str(e)}'}), 500
        
        @self.app.route('/api/videos/<video_id>/status')
        def get_video_status(video_id):
            """Get video processing status"""
            try:
                # Get status from Redis
                status_key = f'video_status:{video_id}'
                status_data = self.redis_client.get(status_key)
                
                if status_data:
                    return jsonify(json.loads(status_data))
                else:
                    return jsonify({'status': 'not_found'}), 404
                    
            except Exception as e:
                logger.error(f"Error getting video status: {e}")
                return jsonify({'error': f'Status error: {str(e)}'}), 500
        
        @self.app.route('/api/videos/<video_id>/events')
        def get_video_events(video_id):
            """Get video events"""
            try:
                # Get query parameters
                start_time = request.args.get('start', type=float)
                end_time = request.args.get('end', type=float)
                event_type = request.args.get('type')
                
                # Query events
                events = self.event_service.get_events(
                    video_id=video_id,
                    start_time=start_time,
                    end_time=end_time,
                    event_type=event_type
                )
                
                return jsonify({'events': events})
                
            except Exception as e:
                logger.error(f"Error getting video events: {e}")
                return jsonify({'error': f'Events error: {str(e)}'}), 500
        
        @self.app.route('/api/videos/<video_id>/clips')
        def get_video_clips(video_id):
            """Get video clips"""
            try:
                start_time = request.args.get('start', type=float)
                end_time = request.args.get('end', type=float)
                
                if not start_time or not end_time:
                    return jsonify({'error': 'Start and end times required'}), 400
                
                # Generate clip
                clip_url = self.video_service.generate_clip(
                    video_id=video_id,
                    start_time=start_time,
                    end_time=end_time
                )
                
                return jsonify({'clip_url': clip_url})
                
            except Exception as e:
                logger.error(f"Error generating clip: {e}")
                return jsonify({'error': f'Clip error: {str(e)}'}), 500
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_endpoint():
            """Chat with AI about video"""
            try:
                data = request.get_json()
                session_id = data.get('session_id')
                message = data.get('message')
                video_id = data.get('video_id')
                
                if not session_id or not message:
                    return jsonify({'error': 'Missing session_id or message'}), 400
                
                # Process message
                if config.is_remote_server:
                    response = self._process_chat_message_remote(session_id, message, video_id)
                else:
                    response = self._process_chat_message_local(session_id, message, video_id)
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Error in chat endpoint: {e}")
                return jsonify({'error': f'Chat error: {str(e)}'}), 500

        @self.app.route('/api/process_video', methods=['POST'])
        def process_video():
            """Process video file (for remote server)"""
            try:
                if 'video' not in request.files:
                    return jsonify({'error': 'No video file provided'}), 400
                
                video_file = request.files['video']
                video_id = request.form.get('video_id')
                
                if video_file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not video_id:
                    return jsonify({'error': 'No video_id provided'}), 400
                
                # Save file
                filename = f"{video_id}_{video_file.filename}"
                filepath = os.path.join(config.storage.local_upload_dir, filename)
                video_file.save(filepath)
                
                # Process video
                result = self._process_video_remote(video_id, filepath)
                
                return jsonify({
                    'video_id': video_id,
                    'filename': filename,
                    'status': 'processing',
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"Error processing video: {e}")
                return jsonify({'error': f'Processing error: {str(e)}'}), 500
    
    def _process_video_remote(self, video_id: str, filepath: str):
        """Process video on remote server"""
        try:
            # Start video processing
            result = self.video_service.process_video(video_id, filepath)
            
            # Start audio processing if enabled
            if config.processing.audio_enabled:
                self.audio_service.process_audio(video_id, filepath)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing video on remote: {e}")
            raise
    
    def _process_video_local(self, video_id: str, filepath: str):
        """Process video on local server (process locally)"""
        try:
            # Process video locally instead of forwarding
            logger.info(f"Processing video locally: {video_id}")
            
            # Start video processing
            result = self.video_service.process_video(video_id, filepath)
            
            # Start audio processing if enabled
            if config.processing.audio_enabled:
                self.audio_service.process_audio(video_id, filepath)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing video locally: {e}")
            raise
    
    def _setup_error_handlers(self):
        """Setup error handlers"""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.errorhandler(413)
        def file_too_large(error):
            return jsonify({'error': 'File too large'}), 413
    
    def run(self, host=None, port=None, debug=None):
        """Run the Flask application"""
        # Validate configuration
        config.validate()
        
        # Set default values
        host = host or config.network.local_host
        port = port or config.network.local_ports[0]
        debug = debug if debug is not None else config.debug
        
        logger.info(f"Starting AI Video Detective on {host}:{port}")
        logger.info(f"Environment: {config.env}")
        logger.info(f"Remote server: {config.is_remote_server}")
        
        # Run with SocketIO
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )

def create_app():
    """Factory function to create Flask app"""
    return AIVideoDetectiveApp()

if __name__ == '__main__':
    app = create_app()
    app.run() 