#!/usr/bin/env python3
"""
PyTorch Compatibility Checker
Checks PyTorch compatibility with SGLang and provides solutions
"""

import subprocess
import sys
import os

def check_torch_version():
    """Check PyTorch version"""
    try:
        import torch
        version = torch.__version__
        print(f"PyTorch version: {version}")
        return version
    except ImportError:
        print("PyTorch not installed")
        return None

def check_sglang_compatibility():
    """Check SGLang compatibility"""
    try:
        import sglang
        print("SGLang is installed")
        return True
    except ImportError:
        print("SGLang not installed")
        return False
    except Exception as e:
        print(f"SGLang compatibility issue: {e}")
        return False

def check_cuda_availability():
    """Check CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA available: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("CUDA not available")
            return False
    except Exception as e:
        print(f"Error checking CUDA: {e}")
        return False

def suggest_solutions():
    """Suggest solutions for compatibility issues"""
    print("\n=== Compatibility Solutions ===")
    print("1. **For SGLang compatibility issues:**")
    print("   - Try reinstalling PyTorch with a compatible version")
    print("   - Use CPU-only mode (already configured)")
    print("   - The application will run in fallback mode")
    
    print("\n2. **For CUDA issues:**")
    print("   - The application is configured to use CPU-only mode")
    print("   - No GPU dependencies required")
    
    print("\n3. **Fallback Mode:**")
    print("   - Application will work without VLM capabilities")
    print("   - Basic video processing and analysis available")
    print("   - Simple responses provided instead of AI-generated ones")

def main():
    """Main function"""
    print("=== PyTorch Compatibility Check ===")
    
    # Check versions
    torch_version = check_torch_version()
    sglang_ok = check_sglang_compatibility()
    cuda_ok = check_cuda_availability()
    
    print(f"\n=== Summary ===")
    print(f"PyTorch: {'✓' if torch_version else '✗'}")
    print(f"SGLang: {'✓' if sglang_ok else '✗'}")
    print(f"CUDA: {'✓' if cuda_ok else '✗'}")
    
    if not sglang_ok:
        print("\n⚠ SGLang compatibility issues detected")
        print("The application will run in fallback mode")
        suggest_solutions()
    else:
        print("\n✓ All compatibility checks passed")
        print("VLM capabilities should work")
    
    print("\nThe application will start regardless of compatibility issues.")

if __name__ == "__main__":
    main() 