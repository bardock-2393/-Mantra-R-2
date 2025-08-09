import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    UPLOAD_FOLDER = 'static/uploads'
    DEVELOPMENT = True  # For cleanup endpoints
    
    # File Upload Configuration - Optimized for 80GB GPU
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm', 'mkv'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB upload limit
    
    # Streaming Upload Configuration
    STREAM_UPLOAD_ENABLED = True
    STREAM_CHUNK_TIMEOUT = 3600  # 1 hour timeout for chunk uploads
    STREAM_CLEANUP_AGE = 3600  # Clean up incomplete uploads after 1 hour
    
    # Redis Configuration
    REDIS_URL = "redis://default:nswO0Z95wT9aeXIIOZMMphnDhsPY3slG@redis-10404.c232.us-east-1-2.ec2.redns.redis-cloud.com:10404"
    
    # AI Model Configuration (Gemma 3)
    # GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # No longer needed for Gemma 3
    
    # Session Configuration
    SESSION_EXPIRY = 3600  # 1 hour in seconds
    UPLOAD_CLEANUP_TIME = 2 * 3600  # 2 hours in seconds
    
    # Analysis Configuration - 80GB GPU Optimized for Sub-1000ms Latency
    MAX_OUTPUT_TOKENS = 128    # Increased for 80GB GPU (more memory available)
    CHAT_MAX_TOKENS = 64       # Increased for better responses with 80GB GPU
    TEMPERATURE = 0.0          # Greedy decoding (fastest)
    CHAT_TEMPERATURE = 0.0     # Greedy decoding (fastest)  
    TOP_P = 1.0               # No nucleus sampling for speed
    TOP_K = 1                 # Greedy selection only (fastest)
    
    # Round 2 Performance Configuration
    TARGET_LATENCY_MS = 1000           # Sub-1000ms requirement
    TARGET_SUCCESS_RATE = 95.0         # 95% success rate target
    CACHE_ENABLED = True               # High-performance caching
    PERFORMANCE_MONITORING = True      # Real-time performance tracking
    
    # Long Video Configuration (120min+ support with 90 FPS) - 80GB GPU Optimized
    LONG_VIDEO_THRESHOLD = 3600        # 1 hour in seconds
    MAX_FRAMES_SHORT_VIDEO = 3         # 80GB GPU: Can handle more frames efficiently
    MAX_FRAMES_LONG_VIDEO = 5          # 80GB GPU: Increased processing capability
    MAX_FILE_SIZE_GB = 2               # 2GB upload limit
    MAX_FPS_SUPPORTED = 90             # Round 2 requirement: 90 FPS support
    
    # 80GB GPU Specific Optimizations
    GPU_MEMORY_GB = 80                 # Available GPU memory
    BATCH_SIZE_OPTIMIZATION = True     # Enable batch processing for 80GB GPU
    PARALLEL_FRAME_PROCESSING = True   # Enable parallel processing
    HIGH_MEMORY_MODE = True            # Enable high memory optimizations
    
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