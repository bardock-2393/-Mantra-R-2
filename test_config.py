#!/usr/bin/env python3
"""
Test Configuration Script
Tests that the configuration is working correctly with environment variables
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test the configuration loading"""
    print("=== Testing Configuration ===")
    
    # Set test environment variables
    os.environ["RAY_NUM_GPUS"] = "0"
    os.environ["IS_REMOTE_SERVER"] = "true"
    os.environ["AUDIO_ENABLED"] = "false"
    
    try:
        from config import config
        
        print("✓ Configuration loaded successfully")
        print(f"  GPU Config - Num GPUs: {config.gpu.num_gpus}")
        print(f"  GPU Config - GPU IDs: {config.gpu.gpu_ids}")
        print(f"  Model Config - LLaVA Device: {config.models.llava_device}")
        print(f"  Model Config - Detection Device: {config.models.detection_device}")
        print(f"  Model Config - TensorRT Enabled: {config.models.tensorrt_enabled}")
        print(f"  Is Remote Server: {config.is_remote_server}")
        print(f"  Processing - Audio Enabled: {config.processing.audio_enabled}")
        
        # Test validation
        try:
            config.validate()
            print("✓ Configuration validation passed")
        except Exception as e:
            print(f"✗ Configuration validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def main():
    """Main function"""
    print("AI Video Detective - Configuration Test")
    print("=" * 50)
    
    success = test_config()
    
    if success:
        print("\n✓ Configuration test passed!")
        print("The application should now work with RAY_NUM_GPUS=0")
    else:
        print("\n✗ Configuration test failed!")
        print("Please check the configuration files and environment variables")

if __name__ == "__main__":
    main() 