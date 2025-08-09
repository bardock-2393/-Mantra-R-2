#!/usr/bin/env python3
"""
Installation script for Gemma 3 dependencies
Run this to install the required packages for Gemma 3 model
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    print("Installing Gemma 3 dependencies...")
    print("=" * 50)
    
    # Required packages for Gemma 3
    packages = [
        "transformers>=4.50.0",
        "torch>=2.0.0",
        "accelerate>=0.20.0"
    ]
    
    success_count = 0
    for package in packages:
        print(f"\nInstalling {package}...")
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Installation completed: {success_count}/{len(packages)} packages installed successfully")
    
    if success_count == len(packages):
        print("✓ All packages installed successfully!")
        print("\nYou can now run the application with Gemma 3 support.")
        print("Note: The first run will download the Gemma 3 model (~25GB)")
    else:
        print("✗ Some packages failed to install. Please check the errors above.")
        print("You may need to install PyTorch manually from https://pytorch.org/")

if __name__ == "__main__":
    main()