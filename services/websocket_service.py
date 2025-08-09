"""
WebSocket Service for Real-time Communication
Handles real-time video analysis, chat updates, and large file uploads for lightning-fast user experience
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import os
import base64
import hashlib
from typing import Dict, Any, Optional
from config import Config

class WebSocketService:
    """Service for managing WebSocket connections and real-time updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.upload_sessions: Dict[str, Dict[str, Any]] = {}  # Track active uploads
        
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
    
    # === WEBSOCKET FILE UPLOAD METHODS ===
    
    def start_upload(self, session_id: str, filename: str, file_size: int, file_type: str) -> Dict[str, Any]:
        """Initialize a new WebSocket file upload session"""
        upload_id = hashlib.md5(f"{session_id}_{filename}_{time.time()}".encode()).hexdigest()
        
        # Validate file size (2GB limit)
        if file_size > Config.MAX_CONTENT_LENGTH:
            return {
                'success': False,
                'error': f'File size ({file_size / (1024**3):.1f}GB) exceeds 2GB limit',
                'upload_id': None
            }
        
        # Validate file type
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return {
                'success': False,
                'error': f'File type .{file_ext} not supported. Use: {", ".join(Config.ALLOWED_EXTENSIONS)}',
                'upload_id': None
            }
        
        # Create upload session
        upload_path = os.path.join(Config.UPLOAD_FOLDER, session_id)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        
        self.upload_sessions[upload_id] = {
            'session_id': session_id,
            'filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'file_path': file_path,
            'bytes_received': 0,
            'chunks_received': 0,
            'started_at': time.time(),
            'status': 'initialized',
            'file_handle': None
        }
        
        # Emit upload started event
        self.socketio.emit('upload_started', {
            'upload_id': upload_id,
            'filename': filename,
            'file_size': file_size,
            'message': f'🚀 Starting upload: {filename} ({file_size / (1024**2):.1f}MB)'
        }, room=session_id)
        
        return {
            'success': True,
            'upload_id': upload_id,
            'message': 'Upload session initialized'
        }
    
    def upload_chunk(self, upload_id: str, chunk_data: str, chunk_index: int, is_final: bool = False) -> Dict[str, Any]:
        """Process a file chunk upload via WebSocket"""
        if upload_id not in self.upload_sessions:
            return {'success': False, 'error': 'Upload session not found'}
        
        upload_session = self.upload_sessions[upload_id]
        session_id = upload_session['session_id']
        
        try:
            # Decode base64 chunk
            chunk_bytes = base64.b64decode(chunk_data)
            chunk_size = len(chunk_bytes)
            
            # Open file handle if first chunk
            if upload_session['file_handle'] is None:
                upload_session['file_handle'] = open(upload_session['file_path'], 'wb')
                upload_session['status'] = 'uploading'
            
            # Write chunk to file
            upload_session['file_handle'].write(chunk_bytes)
            upload_session['bytes_received'] += chunk_size
            upload_session['chunks_received'] += 1
            
            # Calculate progress
            progress = (upload_session['bytes_received'] / upload_session['file_size']) * 100
            upload_speed = upload_session['bytes_received'] / (time.time() - upload_session['started_at']) / (1024**2)  # MB/s
            
            # Emit progress update (with error handling for disconnected clients)
            if session_id in self.active_sessions:
                try:
                    self.socketio.emit('upload_progress', {
                        'upload_id': upload_id,
                        'progress': progress,
                        'bytes_received': upload_session['bytes_received'],
                        'total_size': upload_session['file_size'],
                        'upload_speed': upload_speed,
                        'chunks_received': upload_session['chunks_received'],
                        'message': f'📤 Uploading: {progress:.1f}% ({upload_speed:.1f}MB/s)'
                    }, room=session_id)
                except Exception as e:
                    print(f"⚠️ WebSocket emit error (progress): {e}")
                    # Continue processing even if client disconnected
            else:
                print(f"⚠️ Session {session_id} no longer active, skipping progress update")
            
            # Handle final chunk
            if is_final:
                upload_session['file_handle'].close()
                upload_session['file_handle'] = None
                upload_session['status'] = 'completed'
                
                # Verify file size
                actual_size = os.path.getsize(upload_session['file_path'])
                if actual_size != upload_session['file_size']:
                    return {
                        'success': False,
                        'error': f'File size mismatch: expected {upload_session["file_size"]}, got {actual_size}'
                    }
                
                upload_time = time.time() - upload_session['started_at']
                avg_speed = upload_session['file_size'] / upload_time / (1024**2)
                
                # Emit upload completed event (with error handling)
                if session_id in self.active_sessions:
                    try:
                        self.socketio.emit('upload_completed', {
                            'upload_id': upload_id,
                            'filename': upload_session['filename'],
                            'file_path': upload_session['file_path'],
                            'file_size': upload_session['file_size'],
                            'upload_time': upload_time,
                            'average_speed': avg_speed,
                            'message': f'✅ Upload complete: {upload_session["filename"]} ({avg_speed:.1f}MB/s avg)'
                        }, room=session_id)
                    except Exception as e:
                        print(f"⚠️ WebSocket emit error (completion): {e}")
                        # Upload still completed successfully even if client disconnected
                else:
                    print(f"✅ Upload completed for disconnected session {session_id}: {upload_session['filename']}")
                
                return {
                    'success': True,
                    'file_path': upload_session['file_path'],
                    'upload_complete': True
                }
            
            return {
                'success': True,
                'progress': progress,
                'upload_complete': False
            }
            
        except Exception as e:
            # Cleanup on error
            if upload_session['file_handle']:
                upload_session['file_handle'].close()
            if os.path.exists(upload_session['file_path']):
                os.remove(upload_session['file_path'])
            
            return {
                'success': False,
                'error': f'Upload error: {str(e)}'
            }
    
    def cancel_upload(self, upload_id: str) -> Dict[str, Any]:
        """Cancel an active upload session"""
        if upload_id not in self.upload_sessions:
            return {'success': False, 'error': 'Upload session not found'}
        
        upload_session = self.upload_sessions[upload_id]
        session_id = upload_session['session_id']
        
        # Cleanup file handle and partial file
        if upload_session['file_handle']:
            upload_session['file_handle'].close()
        if os.path.exists(upload_session['file_path']):
            os.remove(upload_session['file_path'])
        
        # Remove upload session
        del self.upload_sessions[upload_id]
        
        # Emit cancellation event
        self.socketio.emit('upload_cancelled', {
            'upload_id': upload_id,
            'message': '❌ Upload cancelled by user'
        }, room=session_id)
        
        return {'success': True, 'message': 'Upload cancelled'}
    
    def get_upload_status(self, upload_id: str) -> Dict[str, Any]:
        """Get current status of an upload session"""
        if upload_id not in self.upload_sessions:
            return {'success': False, 'error': 'Upload session not found'}
        
        upload_session = self.upload_sessions[upload_id]
        progress = (upload_session['bytes_received'] / upload_session['file_size']) * 100
        
        return {
            'success': True,
            'upload_id': upload_id,
            'status': upload_session['status'],
            'progress': progress,
            'bytes_received': upload_session['bytes_received'],
            'total_size': upload_session['file_size'],
            'chunks_received': upload_session['chunks_received']
        }

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