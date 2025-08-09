"""
Session Service Module
Handles Redis session management and data storage
"""

import json
import uuid
import time
import os
from datetime import datetime
import redis
from config import Config

# Configure Redis
redis_client = redis.from_url(Config.REDIS_URL)

def generate_session_id():
    """Generate unique session ID"""
    return str(uuid.uuid4())

def store_session_data(session_id, data):
    """Store session data in Redis"""
    try:
        # Convert complex data types to JSON strings for Redis storage
        redis_data = {}
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                redis_data[key] = json.dumps(value)
            else:
                redis_data[key] = str(value)
        
        redis_client.hset(f"session:{session_id}", mapping=redis_data)
        redis_client.expire(f"session:{session_id}", Config.SESSION_EXPIRY)
    except Exception as e:
        print(f"Redis error: {e}")

def get_session_data(session_id):
    """Get session data from Redis"""
    try:
        data = redis_client.hgetall(f"session:{session_id}")
        # Convert bytes to strings for Windows compatibility
        decoded_data = {}
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            # Try to decode JSON strings back to original types
            try:
                if value.startswith('[') or value.startswith('{'):
                    decoded_data[key] = json.loads(value)
                else:
                    decoded_data[key] = value
            except (json.JSONDecodeError, AttributeError):
                decoded_data[key] = value
                
        return decoded_data
    except Exception as e:
        print(f"Redis error: {e}")
        return {}

def cleanup_session_data(session_id):
    """Clean up all session data from Redis and delete uploaded files"""
    try:
        # Get session data to find uploaded files
        session_data = get_session_data(session_id)
        
        # Delete uploaded video file
        if session_data and 'filepath' in session_data:
            video_path = session_data['filepath']
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"Deleted video file: {video_path}")
                except Exception as e:
                    print(f"Error deleting video file {video_path}: {e}")
        
        # Delete all screenshots and video clips for this session
        upload_folder = Config.UPLOAD_FOLDER
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.startswith(f"screenshot_{session_id}_") or filename.startswith(f"clip_{session_id}_"):
                    file_path = os.path.join(upload_folder, filename)
                    try:
                        os.remove(file_path)
                        print(f"Deleted evidence file: {filename}")
                    except Exception as e:
                        print(f"Error deleting evidence file {filename}: {e}")
        
        # Delete session data from Redis
        try:
            redis_client.delete(f"session:{session_id}")
            print(f"Deleted session data from Redis: {session_id}")
        except Exception as e:
            print(f"Error deleting session data from Redis: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error during session cleanup: {e}")
        return False

def cleanup_expired_sessions():
    """Clean up expired sessions (older than 1 hour)"""
    try:
        # Get all session keys from Redis
        session_keys = redis_client.keys("session:*")
        
        for key in session_keys:
            session_id = key.decode('utf-8').replace('session:', '')
            
            # Check if session is expired (older than 1 hour)
            ttl = redis_client.ttl(key)
            if ttl == -1:  # No expiration set, set it now
                redis_client.expire(key, Config.SESSION_EXPIRY)
            elif ttl == -2:  # Key doesn't exist
                continue
            elif ttl == 0:  # Expired, clean it up
                cleanup_session_data(session_id)
        
        print("Expired sessions cleanup completed")
        
    except Exception as e:
        print(f"Error during expired sessions cleanup: {e}")

def cleanup_old_uploads():
    """Clean up old upload files and evidence (older than 2 hours)"""
    try:
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            return
        
        current_time = time.time()
        cutoff_time = current_time - Config.UPLOAD_CLEANUP_TIME
        
        files_cleaned = 0
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
            
            # Check file modification time
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff_time:
                try:
                    os.remove(file_path)
                    files_cleaned += 1
                    print(f"Cleaned up old file: {filename}")
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
        
        if files_cleaned > 0:
            print(f"Cleaned up {files_cleaned} old files from uploads folder")
        
    except Exception as e:
        print(f"Error during uploads cleanup: {e}")

def get_all_session_keys():
    """Get all session keys from Redis"""
    try:
        session_keys = redis_client.keys("session:*")
        return [key.decode('utf-8').replace('session:', '') for key in session_keys]
    except Exception as e:
        print(f"Error getting session keys: {e}")
        return [] 