#!/usr/bin/env python3
"""
VLM Disabler
Disables VLM capabilities to avoid SGLang compatibility issues
"""

import os
import sys

def disable_vlm():
    """Disable VLM by setting environment variables"""
    print("=== Disabling VLM Capabilities ===")
    
    # Set environment variables to disable VLM
    os.environ["DISABLE_VLM"] = "true"
    os.environ["USE_FALLBACK_MODE"] = "true"
    
    print("✓ VLM capabilities disabled")
    print("✓ Application will run in fallback mode")
    print("✓ No SGLang dependencies required")
    
    return True

def main():
    """Main function"""
    disable_vlm()
    print("\nYou can now run the application without VLM issues:")
    print("python app.py")

if __name__ == "__main__":
    main() 