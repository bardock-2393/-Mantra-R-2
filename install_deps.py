#!/usr/bin/env python3
"""
Dependency Installation Script
Installs missing dependencies for the AI Video Detective application
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

def main():
    """Main function to install dependencies"""
    print("=== AI Video Detective - Dependency Installation ===")
    
    # List of required packages
    required_packages = [
        "orjson==3.9.10",
        "uvloop==0.19.0"
    ]
    
    print("Installing missing dependencies...")
    
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\nInstallation complete: {success_count}/{len(required_packages)} packages installed")
    
    if success_count == len(required_packages):
        print("✓ All dependencies installed successfully!")
        print("The application should now work with VLM capabilities.")
    else:
        print("⚠ Some dependencies failed to install.")
        print("The application will run in fallback mode without VLM capabilities.")
    
    print("\nYou can now run: start_server.bat")

if __name__ == "__main__":
    main() 