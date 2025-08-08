import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GPUConfig:
    """GPU configuration for distributed processing"""
    num_gpus: int = 7
    gpu_memory_gb: int = 80
    gpu_ids: List[int] = None
    
    def __post_init__(self):
        if self.gpu_ids is None:
            self.gpu_ids = list(range(self.num_gpus))

@dataclass
class ModelConfig:
    """AI model configuration"""
    # VLM Models
    llava_model: str = "llava-hf/LLaVA-NeXT-Video-7B-hf"
    llava_device: str = "cuda:5"  # GPU 5 for VLM
    
    # Object Detection Models
    detection_model: str = "RT-DETR-v2"
    detection_device: str = "cuda:0"  # GPU 0-3 for detection
    
    # Audio Models
    whisper_model: str = "base"  # base, small, medium, large
    audioclip_model: str = "default"
    wav2vec2_model: str = "facebook/wav2vec2-base"
    
    # TensorRT Optimization
    tensorrt_enabled: bool = True
    tensorrt_precision: str = "fp16"  # fp16, int8
    tensorrt_engine_dir: str = "./tensorrt_engines"

@dataclass
class ProcessingConfig:
    """Video and audio processing configuration"""
    # Video Processing
    target_fps: int = 90
    adaptive_sampling: bool = True
    global_fps: int = 6
    motion_fps: int = 16
    change_fps: int = 24
    
    # Audio Processing
    audio_enabled: bool = True
    audio_sample_rate: int = 16000
    audio_chunk_duration: float = 30.0  # seconds
    
    # Window Processing
    window_seconds: int = 20
    overlap_seconds: int = 2
    
    # Multi-modal
    temporal_alignment: bool = True
    audio_visual_sync: bool = True

@dataclass
class StorageConfig:
    """Storage and database configuration"""
    # Local Storage
    local_upload_dir: str = "./static/uploads"
    local_temp_dir: str = "./temp"
    
    # Remote Storage
    remote_storage_url: str = os.getenv("REMOTE_STORAGE_URL", "s3://ai-video-detective")
    use_s3: bool = os.getenv("USE_S3", "false").lower() == "true"
    
    # Database
    duckdb_path: str = os.getenv("DUCKDB_PATH", "./data/events.duckdb")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File Formats
    supported_video_formats: List[str] = None
    supported_audio_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_video_formats is None:
            self.supported_video_formats = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
        if self.supported_audio_formats is None:
            self.supported_audio_formats = [".wav", ".mp3", ".aac", ".flac", ".ogg"]

@dataclass
class NetworkConfig:
    """Network and API configuration"""
    # Local Development Environment
    local_host: str = "0.0.0.0"
    local_ports: List[int] = None
    
    # API Configuration
    api_timeout: int = 30
    max_file_size: int = 1024 * 1024 * 1024  # 1GB
    chunk_size: int = 8192
    
    # WebSocket
    websocket_ping_timeout: int = 10
    websocket_ping_interval: int = 25
    
    def __post_init__(self):
        if self.local_ports is None:
            self.local_ports = [8888, 8080, 8000]

@dataclass
class AnalysisConfig:
    """Analysis and rules configuration"""
    # Analysis Types
    analysis_types: List[str] = None
    
    # Rules Engine
    rules_enabled: bool = True
    domain_agnostic: bool = True
    
    # Event Detection
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    
    # Performance Targets
    target_query_latency_ms: int = 600
    target_throughput_fps: int = 90
    
    def __post_init__(self):
        if self.analysis_types is None:
            self.analysis_types = [
                "comprehensive_analysis",
                "safety_investigation", 
                "performance_analysis",
                "pattern_detection",
                "creative_review"
            ]

@dataclass
class SecurityConfig:
    """Security and access control"""
    # Access Control
    allowed_ips: List[str] = None
    api_key_required: bool = False
    cors_origins: List[str] = None
    
    # File Security
    scan_uploads: bool = True
    max_file_count: int = 100
    
    def __post_init__(self):
        if self.allowed_ips is None:
            self.allowed_ips = ["127.0.0.1", "localhost", "0.0.0.0"]
        if self.cors_origins is None:
            self.cors_origins = [
                "*",
                "http://localhost:8888",
                "http://localhost:8080", 
                "http://localhost:8000",
                "http://127.0.0.1:8888",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8000"
            ]

class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Environment
        self.env = os.getenv("ENV", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Distributed Architecture
        self.is_remote_server = os.getenv("IS_REMOTE_SERVER", "false").lower() == "true"
        self.remote_gpu_server_url = os.getenv("REMOTE_GPU_SERVER_URL", "http://localhost:8001")
        
        # Configuration Objects
        self.gpu = GPUConfig()
        self.models = ModelConfig()
        self.processing = ProcessingConfig()
        self.storage = StorageConfig()
        self.network = NetworkConfig()
        self.analysis = AnalysisConfig()
        self.security = SecurityConfig()
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        # GPU Configuration
        if os.getenv("NUM_GPUS"):
            self.gpu.num_gpus = int(os.getenv("NUM_GPUS"))
        
        # Model Configuration
        if os.getenv("LLAVA_MODEL"):
            self.models.llava_model = os.getenv("LLAVA_MODEL")
        if os.getenv("WHISPER_MODEL"):
            self.models.whisper_model = os.getenv("WHISPER_MODEL")
        
        # Processing Configuration
        if os.getenv("WINDOW_SECONDS"):
            self.processing.window_seconds = int(os.getenv("WINDOW_SECONDS"))
        if os.getenv("AUDIO_ENABLED"):
            self.processing.audio_enabled = os.getenv("AUDIO_ENABLED").lower() == "true"
        
        # Storage Configuration
        if os.getenv("LOCAL_UPLOAD_DIR"):
            self.storage.local_upload_dir = os.getenv("LOCAL_UPLOAD_DIR")
        if os.getenv("DUCKDB_PATH"):
            self.storage.duckdb_path = os.getenv("DUCKDB_PATH")
        
        # Network Configuration
        if os.getenv("LOCAL_PORTS"):
            ports_str = os.getenv("LOCAL_PORTS")
            self.network.local_ports = [int(p.strip()) for p in ports_str.split(",")]
        
        # Analysis Configuration
        if os.getenv("ANALYSIS_TYPES"):
            types_str = os.getenv("ANALYSIS_TYPES")
            self.analysis.analysis_types = [t.strip() for t in types_str.split(",")]
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD"),
            "decode_responses": True
        }
    
    def get_ray_config(self) -> Dict[str, Any]:
        """Get Ray configuration for distributed processing"""
        ray_address = os.getenv("RAY_ADDRESS", "localhost:10001")
        
        # Base configuration - minimal for connecting to existing cluster
        config = {
            "address": ray_address,
            "dashboard_host": "0.0.0.0",
            "dashboard_port": 8265
        }
        
        # Only add resource parameters if starting a new cluster
        # If RAY_ADDRESS is "auto", add resources for new cluster
        if ray_address == "auto":
            config.update({
                "num_cpus": int(os.getenv("RAY_NUM_CPUS", "8")),
                "num_gpus": self.gpu.num_gpus,
                "object_store_memory": int(os.getenv("RAY_OBJECT_STORE_MEMORY", "1000000000")),  # 1GB
            })
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration"""
        # Check required directories
        os.makedirs(self.storage.local_upload_dir, exist_ok=True)
        os.makedirs(self.storage.local_temp_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.storage.duckdb_path), exist_ok=True)
        
        # Check GPU availability
        if self.is_remote_server:
            try:
                import torch
                if not torch.cuda.is_available():
                    raise ValueError("CUDA not available on remote server")
                if torch.cuda.device_count() < self.gpu.num_gpus:
                    raise ValueError(f"Not enough GPUs available. Required: {self.gpu.num_gpus}, Available: {torch.cuda.device_count()}")
            except ImportError:
                raise ImportError("PyTorch not installed")
        
        return True

# Global configuration instance
config = Config() 