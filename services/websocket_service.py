"""
WebSocket Service for Real-time Communication
Handles real-time video analysis and chat updates for lightning-fast user experience
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
import time
from typing import Dict, Any, Optional

class WebSocketService:
    """Service for managing WebSocket connections and real-time updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    def join_session(self, session_id: str, sid: str):
        """Join a session room for real-time updates"""
        join_room(session_id, sid=sid)
        self.active_sessions[session_id] = {
            'sid': sid,
            'connected_at': time.time(),
            'status': 'connected'
        }
        
        # Send connection confirmation
        self.socketio.emit('session_joined', {
            'session_id': session_id,
            'status': 'connected',
            'message': '🔗 Real-time connection established - Ready for lightning-fast analysis!'
        }, room=session_id)
    
    def leave_session(self, session_id: str, sid: str):
        """Leave a session room"""
        leave_room(session_id, sid=sid)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def emit_progress(self, session_id: str, stage: str, progress: float, message: str):
        """Emit analysis progress updates in real-time"""
        if session_id in self.active_sessions:
            self.socketio.emit('analysis_progress', {
                'stage': stage,
                'progress': progress,
                'message': message,
                'timestamp': time.time()
            }, room=session_id)
    
    def emit_frame_extracted(self, session_id: str, frame_count: int, total_frames: int, duration: float):
        """Emit frame extraction progress for long videos"""
        if session_id in self.active_sessions:
            progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
            self.emit_progress(
                session_id, 
                'frame_extraction', 
                progress,
                f'🎬 Extracted {frame_count}/{total_frames} frames ({duration:.1f}s video)'
            )
    
    def emit_ai_thinking(self, session_id: str, stage: str = 'ai_inference'):
        """Emit AI thinking status"""
        if session_id in self.active_sessions:
            self.socketio.emit('ai_thinking', {
                'stage': stage,
                'message': '🧠 Gemma 3 AI is analyzing your content...',
                'timestamp': time.time()
            }, room=session_id)
    
    def emit_analysis_complete(self, session_id: str, result: str, timing_info: Dict[str, float]):
        """Emit completed analysis with results"""
        if session_id in self.active_sessions:
            self.socketio.emit('analysis_complete', {
                'result': result,
                'timing': timing_info,
                'timestamp': time.time()
            }, room=session_id)
    
    def emit_chat_response(self, session_id: str, response: str, timing_info: Dict[str, float]):
        """Emit real-time chat response"""
        if session_id in self.active_sessions:
            self.socketio.emit('chat_response', {
                'response': response,
                'timing': timing_info,
                'timestamp': time.time()
            }, room=session_id)
    
    def emit_error(self, session_id: str, error: str, stage: str = 'general'):
        """Emit error to client"""
        if session_id in self.active_sessions:
            self.socketio.emit('error', {
                'error': error,
                'stage': stage,
                'timestamp': time.time()
            }, room=session_id)
    
    def emit_long_video_detected(self, session_id: str, duration_minutes: float):
        """Emit notification for long video detection"""
        if session_id in self.active_sessions:
            self.socketio.emit('long_video_detected', {
                'duration_minutes': duration_minutes,
                'message': f'🎬 Long video detected ({duration_minutes:.1f} minutes) - Using smart sampling for optimal speed!',
                'timestamp': time.time()
            }, room=session_id)

# Global WebSocket service instance
websocket_service: Optional[WebSocketService] = None

def initialize_websocket_service(socketio: SocketIO) -> WebSocketService:
    """Initialize the global WebSocket service"""
    global websocket_service
    websocket_service = WebSocketService(socketio)
    return websocket_service

def get_websocket_service() -> Optional[WebSocketService]:
    """Get the global WebSocket service instance"""
    return websocket_service