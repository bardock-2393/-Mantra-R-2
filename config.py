import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # File Upload Configuration
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm', 'mkv'}
    
    # Redis Configuration
    REDIS_URL = "redis://default:nswO0Z95wT9aeXIIOZMMphnDhsPY3slG@redis-10404.c232.us-east-1-2.ec2.redns.redis-cloud.com:10404"
    
    # AI Model Configuration (Gemma 3)
    # GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # No longer needed for Gemma 3
    
    # Session Configuration
    SESSION_EXPIRY = 3600  # 1 hour in seconds
    UPLOAD_CLEANUP_TIME = 2 * 3600  # 2 hours in seconds
    
    # Analysis Configuration
    MAX_OUTPUT_TOKENS = 32768
    CHAT_MAX_TOKENS = 8192
    TEMPERATURE = 0.2
    CHAT_TEMPERATURE = 0.3
    TOP_P = 0.9
    TOP_K = 40
    
    # Default Video Configuration
    DEFAULT_VIDEO_PATH = 'BMW M4 - Ultimate Racetrack - BMW Canada (720p, h264).mp4'

# Enhanced Agent Capabilities
AGENT_CAPABILITIES = {
    "autonomous_analysis": True,
    "multi_modal_understanding": True,
    "context_aware_responses": True,
    "proactive_insights": True,
    "comprehensive_reporting": True,
    "adaptive_focus": True
}

# Agent Tools and Capabilities
AGENT_TOOLS = {
    "video_analysis": {
        "description": "Comprehensive video content analysis with multi-modal understanding",
        "capabilities": ["visual_analysis", "audio_analysis", "temporal_analysis", "spatial_analysis"]
    },
    "context_awareness": {
        "description": "Advanced context understanding and adaptive responses",
        "capabilities": ["session_memory", "conversation_history", "user_preferences", "analysis_context"]
    },
    "autonomous_workflow": {
        "description": "Self-directed analysis and proactive insights generation",
        "capabilities": ["autonomous_analysis", "proactive_insights", "adaptive_focus", "comprehensive_reporting"]
    }
} 