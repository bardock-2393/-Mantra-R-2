#!/usr/bin/env python3
"""
Ray Cluster Resource Management Script
Helps manage and optimize Ray cluster resources to prevent exhaustion
"""

import os
import sys
import ray
import psutil
import logging
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_system_resources() -> Dict[str, Any]:
    """Get current system resource usage"""
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Check for GPUs
    gpu_count = 0
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
    except ImportError:
        pass
    
    return {
        'cpu_count': cpu_count,
        'memory_gb': memory_gb,
        'gpu_count': gpu_count,
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent
    }

def optimize_ray_config() -> Dict[str, Any]:
    """Create optimized Ray configuration based on system resources"""
    resources = get_system_resources()
    
    # Conservative resource allocation (50% of available)
    cpu_limit = max(1, int(resources['cpu_count'] * 0.5))
    memory_limit = max(1, int(resources['memory_gb'] * 0.5))
    gpu_limit = max(0, int(resources['gpu_count'] * 0.5))
    
    # Reduce GPU usage if system is under load
    if resources['cpu_percent'] > 80 or resources['memory_percent'] > 80:
        gpu_limit = max(0, gpu_limit - 1)
        cpu_limit = max(1, cpu_limit - 1)
    
    config = {
        'num_cpus': cpu_limit,
        'num_gpus': gpu_limit,
        'object_store_memory': min(1000000000, int(memory_limit * 0.3 * 1024**3)),  # 30% of memory
        'dashboard_host': '0.0.0.0',
        'dashboard_port': 8265,
        'include_dashboard': True,
        'log_to_driver': True,
        'local_mode': False,
        'ignore_reinit_error': True
    }
    
    logger.info(f"Optimized Ray config: {config}")
    return config

def cleanup_ray_actors():
    """Clean up existing Ray actors to free resources"""
    try:
        if ray.is_initialized():
            # Get all actors
            actors = ray.get_actor_names()
            logger.info(f"Found {len(actors)} actors")
            
            # Terminate actors (be careful with this in production)
            for actor_name in actors:
                try:
                    actor = ray.get_actor(actor_name)
                    ray.kill(actor)
                    logger.info(f"Terminated actor: {actor_name}")
                except Exception as e:
                    logger.warning(f"Could not terminate actor {actor_name}: {e}")
                    
    except Exception as e:
        logger.error(f"Error cleaning up actors: {e}")

def restart_ray_cluster():
    """Restart Ray cluster with optimized configuration"""
    try:
        # Shutdown existing cluster
        if ray.is_initialized():
            logger.info("Shutting down existing Ray cluster...")
            ray.shutdown()
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Get optimized config
        config = optimize_ray_config()
        
        # Initialize new cluster
        logger.info("Starting new Ray cluster with optimized configuration...")
        ray.init(**config)
        
        logger.info("Ray cluster restarted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error restarting Ray cluster: {e}")
        return False

def check_ray_health() -> bool:
    """Check if Ray cluster is healthy"""
    try:
        if not ray.is_initialized():
            logger.warning("Ray is not initialized")
            return False
        
        # Test basic functionality
        @ray.remote
        def test_function():
            return "OK"
        
        result = ray.get(test_function.remote())
        if result == "OK":
            logger.info("Ray cluster is healthy")
            return True
        else:
            logger.warning("Ray cluster test failed")
            return False
            
    except Exception as e:
        logger.error(f"Ray health check failed: {e}")
        return False

def main():
    """Main function"""
    print("=== Ray Cluster Resource Management ===")
    
    # Show current system resources
    resources = get_system_resources()
    print(f"System Resources:")
    print(f"  CPUs: {resources['cpu_count']} (Usage: {resources['cpu_percent']:.1f}%)")
    print(f"  Memory: {resources['memory_gb']:.1f}GB (Usage: {resources['memory_percent']:.1f}%)")
    print(f"  GPUs: {resources['gpu_count']}")
    
    # Check if Ray is running
    if ray.is_initialized():
        print("\nRay cluster is currently running")
        
        # Check health
        if check_ray_health():
            print("Ray cluster is healthy")
        else:
            print("Ray cluster has issues, attempting restart...")
            if restart_ray_cluster():
                print("Ray cluster restarted successfully")
            else:
                print("Failed to restart Ray cluster")
    else:
        print("\nRay cluster is not running, starting with optimized config...")
        if restart_ray_cluster():
            print("Ray cluster started successfully")
        else:
            print("Failed to start Ray cluster")
    
    print("\n=== Resource Management Complete ===")

if __name__ == "__main__":
    main() 