#!/usr/bin/env python3
"""
GPU Device Check and Fix Script
"""

import torch
import os

def check_gpu_devices():
    """Check available GPU devices"""
    print("🔍 Checking GPU devices...")
    
    if not torch.cuda.is_available():
        print("❌ CUDA not available")
        return 0
    
    gpu_count = torch.cuda.device_count()
    print(f"✅ Found {gpu_count} GPU(s)")
    
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
    
    return gpu_count

def fix_config_for_gpus(gpu_count):
    """Fix configuration for available GPUs"""
    print(f"\n🔧 Fixing configuration for {gpu_count} GPU(s)...")
    
    # Update environment variables
    os.environ['NUM_GPUS'] = str(gpu_count)
    
    # Set device mappings based on available GPUs
    if gpu_count >= 1:
        os.environ['DETECTION_DEVICE'] = 'cuda:0'
    if gpu_count >= 2:
        os.environ['LLAVA_DEVICE'] = 'cuda:1'
    else:
        os.environ['LLAVA_DEVICE'] = 'cuda:0'
    
    print("✅ Configuration updated")
    print(f"   Detection device: {os.environ.get('DETECTION_DEVICE', 'cuda:0')}")
    print(f"   LLaVA device: {os.environ.get('LLAVA_DEVICE', 'cuda:0')}")

if __name__ == "__main__":
    gpu_count = check_gpu_devices()
    if gpu_count > 0:
        fix_config_for_gpus(gpu_count)
        print("\n🚀 Now try running: python main.py")
    else:
        print("\n❌ No GPUs available. Check CUDA installation.") 