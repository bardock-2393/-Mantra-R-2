#!/bin/bash

# AI Video Detective - Fixed Startup Script
# This script fixes Ray cluster issues and starts the application properly

set -e

echo "=== AI Video Detective - Fixed Startup ==="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found. Please run this script from the ai_video_detective2 directory."
    exit 1
fi

# Set environment variables for better resource management
export RAY_NUM_CPUS=4
export RAY_NUM_GPUS=1
export RAY_OBJECT_STORE_MEMORY=500000000
export ENV=development
export DEBUG=true
export IS_REMOTE_SERVER=false
export REMOTE_GPU_SERVER_URL=http://localhost:8001

echo "Environment variables set:"
echo "  RAY_NUM_CPUS=$RAY_NUM_CPUS"
echo "  RAY_NUM_GPUS=$RAY_NUM_GPUS"
echo "  RAY_OBJECT_STORE_MEMORY=$RAY_OBJECT_STORE_MEMORY"
echo "  IS_REMOTE_SERVER=$IS_REMOTE_SERVER"

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade required packages
echo "Installing/upgrading packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Fix Ray cluster issues
echo "Fixing Ray cluster issues..."
python fix_ray_resources.py

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p static/uploads
mkdir -p temp
mkdir -p data

# Start the application
echo "Starting AI Video Detective..."
echo "Access the application at: http://localhost:8888"
echo "Press Ctrl+C to stop"

python app.py 