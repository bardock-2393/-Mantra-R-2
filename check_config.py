#!/usr/bin/env python3
"""
Configuration Checker
Checks current configuration and Ray status
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check environment variables"""
    print("=== Environment Variables ===")
    env_vars = [
        'ENV', 'DEBUG', 'IS_REMOTE_SERVER', 'REMOTE_GPU_SERVER_URL',
        'RAY_NUM_CPUS', 'RAY_NUM_GPUS', 'RAY_OBJECT_STORE_MEMORY',
        'AUDIO_ENABLED', 'WINDOW_SECONDS'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        print(f"  {var}: {value}")

def check_config():
    """Check application configuration"""
    try:
        from config import config
        print("\n=== Application Configuration ===")
        print(f"  Environment: {config.env}")
        print(f"  Debug: {config.debug}")
        print(f"  Is Remote Server: {config.is_remote_server}")
        print(f"  Remote GPU Server URL: {config.remote_gpu_server_url}")
        print(f"  GPU Config - Num GPUs: {config.gpu.num_gpus}")
        print(f"  GPU Config - GPU IDs: {config.gpu.gpu_ids}")
        print(f"  Processing - Audio Enabled: {config.processing.audio_enabled}")
        print(f"  Processing - Window Seconds: {config.processing.window_seconds}")
        print(f"  Network - Local Ports: {config.network.local_ports}")
        print(f"  Security - CORS Origins: {config.security.cors_origins}")
        
    except Exception as e:
        print(f"Error loading config: {e}")

def check_ray():
    """Check Ray status"""
    print("\n=== Ray Status ===")
    try:
        import ray
        if ray.is_initialized():
            print("  Ray is initialized")
            try:
                # Get Ray cluster info
                cluster_resources = ray.cluster_resources()
                print(f"  Cluster Resources: {cluster_resources}")
                
                # Get available resources
                available_resources = ray.available_resources()
                print(f"  Available Resources: {available_resources}")
                
            except Exception as e:
                print(f"  Error getting Ray info: {e}")
        else:
            print("  Ray is not initialized")
            
    except ImportError:
        print("  Ray is not installed")
    except Exception as e:
        print(f"  Error checking Ray: {e}")

def check_directories():
    """Check if required directories exist"""
    print("\n=== Directory Check ===")
    directories = [
        'static/uploads',
        'temp',
        'data',
        'templates',
        'static/css',
        'static/js'
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"  ✓ {directory}")
        else:
            print(f"  ✗ {directory} (missing)")

def main():
    """Main function"""
    print("AI Video Detective - Configuration Check")
    print("=" * 50)
    
    check_environment()
    check_config()
    check_ray()
    check_directories()
    
    print("\n=== Summary ===")
    print("If you see any issues above, please fix them before starting the application.")
    print("Use 'start_server.bat' to start the application in server mode.")

if __name__ == "__main__":
    main() 