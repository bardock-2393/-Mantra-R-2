"""
Session Service for managing user sessions and conversation context
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import redis

from utils.logger import setup_logger

logger = setup_logger(__name__)

class SessionService:
    """Service for managing user sessions and conversation context"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.session_timeout = 3600  # 1 hour in seconds
        self.max_context_length = 50  # Maximum conversation history entries
    
    def create_session(self, session_id: str = None) -> Dict[str, Any]:
        """Create a new session or get existing session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check if session exists
        session_data = self.get_session(session_id)
        if session_data:
            return session_data
        
        # Create new session
        session_data = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'context': [],
            'video_id': None,
            'analysis_type': None,
            'status': 'active'
        }
        
        # Store in Redis
        self._store_session(session_id, session_data)
        
        logger.info(f"Created new session: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID"""
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                session = json.loads(session_data)
                
                # Check if session is expired
                last_activity = datetime.fromisoformat(session['last_activity'])
                if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
                    logger.info(f"Session expired: {session_id}")
                    self.cleanup_session(session_id)
                    return None
                
                # Update last activity
                session['last_activity'] = datetime.now().isoformat()
                self._store_session(session_id, session)
                
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session_data['last_activity'] = datetime.now().isoformat()
            self._store_session(session_id, session_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def add_message_to_context(self, session_id: str, user_message: str, assistant_response: str) -> bool:
        """Add a message exchange to session context"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Add new message to context
            context_entry = {
                'user': user_message,
                'assistant': assistant_response,
                'timestamp': datetime.now().isoformat()
            }
            
            session['context'].append(context_entry)
            
            # Limit context length
            if len(session['context']) > self.max_context_length:
                session['context'] = session['context'][-self.max_context_length:]
            
            # Update session
            return self.update_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Error adding message to context: {e}")
            return False
    
    def set_video_context(self, session_id: str, video_id: str) -> bool:
        """Set the video context for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session['video_id'] = video_id
            return self.update_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Error setting video context: {e}")
            return False
    
    def set_analysis_type(self, session_id: str, analysis_type: str) -> bool:
        """Set the analysis type for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session['analysis_type'] = analysis_type
            return self.update_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Error setting analysis type: {e}")
            return False
    
    def get_session_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the conversation context for a session"""
        try:
            session = self.get_session(session_id)
            if session:
                return session.get('context', [])
            return []
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return []
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session"""
        try:
            session_key = f"session:{session_id}"
            self.redis_client.delete(session_key)
            logger.info(f"Cleaned up session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions"""
        try:
            cleaned_count = 0
            pattern = "session:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        session = json.loads(session_data)
                        last_activity = datetime.fromisoformat(session['last_activity'])
                        
                        if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
                            self.redis_client.delete(key)
                            cleaned_count += 1
                            
                except Exception as e:
                    logger.error(f"Error processing session key {key}: {e}")
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        try:
            active_sessions = []
            pattern = "session:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        session = json.loads(session_data)
                        last_activity = datetime.fromisoformat(session['last_activity'])
                        
                        if datetime.now() - last_activity <= timedelta(seconds=self.session_timeout):
                            active_sessions.append(session)
                            
                except Exception as e:
                    logger.error(f"Error processing session key {key}: {e}")
                    continue
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            total_sessions = 0
            active_sessions = 0
            expired_sessions = 0
            pattern = "session:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        total_sessions += 1
                        session = json.loads(session_data)
                        last_activity = datetime.fromisoformat(session['last_activity'])
                        
                        if datetime.now() - last_activity <= timedelta(seconds=self.session_timeout):
                            active_sessions += 1
                        else:
                            expired_sessions += 1
                            
                except Exception as e:
                    logger.error(f"Error processing session key {key}: {e}")
                    continue
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'expired_sessions': expired_sessions,
                'session_timeout_seconds': self.session_timeout
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    def _store_session(self, session_id: str, session_data: Dict[str, Any]):
        """Store session data in Redis"""
        session_key = f"session:{session_id}"
        session_json = json.dumps(session_data)
        
        # Store with expiration
        self.redis_client.setex(
            session_key,
            self.session_timeout,
            session_json
        ) 