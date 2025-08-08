#!/usr/bin/env python3
"""
Environment Variable Loader
Loads environment variables from server.env file
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file_path):
    """Load environment variables from .env file"""
    if not os.path.exists(env_file_path):
        print(f"Warning: {env_file_path} not found")
        return
    
    print(f"Loading environment from: {env_file_path}")
    
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value
                print(f"  {key}={value}")

def main():
    """Main function to load environment variables"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Load server.env if it exists
    server_env_path = script_dir / "server.env"
    load_env_file(server_env_path)
    
    # Also load .env if it exists
    env_path = script_dir / ".env"
    load_env_file(env_path)
    
    print("Environment variables loaded successfully")

if __name__ == "__main__":
    main() 