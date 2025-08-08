#!/usr/bin/env python3
"""
AI Video Detective - Main Entry Point
Distributed Architecture with Local Development Environment and Remote GPU Server
"""

import os
import sys
import argparse
import signal
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def setup_environment():
    """Setup environment and validate configuration"""
    try:
        # Create necessary directories
        directories = [
            config.storage.local_upload_dir,
            config.storage.local_temp_dir,
            os.path.dirname(config.storage.duckdb_path),
            "logs",
            "data"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Validate configuration
        config.validate()
        
        logger.info("Environment setup completed successfully")
        
    except Exception as e:
        logger.error(f"Environment setup failed: {e}")
        raise

def run_local_server():
    """Run the local development server"""
    try:
        logger.info("Starting AI Video Detective - Local Development Server")
        logger.info(f"Environment: {config.env}")
        logger.info(f"Debug mode: {config.debug}")
        logger.info(f"Remote server: {config.remote_gpu_server_url}")
        
        # Create Flask app
        app = create_app()
        
        # Run the application
        app.run(
            host=config.network.local_host,
            port=config.network.local_ports[0],
            debug=config.debug
        )
        
    except Exception as e:
        logger.error(f"Failed to start local server: {e}")
        raise

def run_remote_server():
    """Run the remote GPU server"""
    try:
        logger.info("Starting AI Video Detective - Remote GPU Server")
        logger.info(f"Environment: {config.env}")
        logger.info(f"Debug mode: {config.debug}")
        logger.info(f"GPU count: {config.gpu.num_gpus}")
        
        # Import and run remote server components
        from services.ai_service import AIService
        from services.video_service import VideoService
        from services.audio_service import AudioService
        
        # Initialize services
        ai_service = AIService(config)
        video_service = VideoService(config)
        audio_service = AudioService(config)
        
        # Create Flask app for remote API
        app = create_app()
        
        # Run the application
        app.run(
            host=config.network.local_host,
            port=8001,  # Remote server port
            debug=config.debug
        )
        
    except Exception as e:
        logger.error(f"Failed to start remote server: {e}")
        raise

def run_worker():
    """Run a background worker for processing tasks"""
    try:
        logger.info("Starting AI Video Detective - Background Worker")
        
        # Import worker components
        import ray
        from services.video_service import VideoService
        from services.audio_service import AudioService
        
        # Initialize Ray
        if not ray.is_initialized():
            ray_config = config.get_ray_config()
            ray.init(**ray_config)
        
        # Initialize services
        video_service = VideoService(config)
        audio_service = AudioService(config)
        
        logger.info("Worker started successfully")
        
        # Keep worker running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AI Video Detective')
    parser.add_argument('--mode', choices=['local', 'remote', 'worker'], 
                       default='local', help='Server mode')
    parser.add_argument('--host', default=None, help='Host address')
    parser.add_argument('--port', type=int, default=None, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup environment
        setup_environment()
        
        # Override config with command line arguments
        if args.host:
            config.network.local_host = args.host
        if args.port:
            config.network.local_ports[0] = args.port
        if args.debug:
            config.debug = True
        
        # Run appropriate mode
        if args.mode == 'local':
            run_local_server()
        elif args.mode == 'remote':
            run_remote_server()
        elif args.mode == 'worker':
            run_worker()
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 