#!/bin/bash

# AI Video Detective - Remote GPU Server Startup Script

echo "🚀 Starting AI Video Detective - Remote GPU Server"
echo "=================================================="

# Check if running on GPU server
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ Error: NVIDIA drivers not found. This script should run on a GPU server."
    exit 1
fi

# Check GPU availability
echo "🔍 Checking GPU availability..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits

# Check CUDA availability
if ! python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')" 2>/dev/null; then
    echo "❌ Error: PyTorch with CUDA not available. Please install PyTorch with CUDA support."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements_server.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/uploads temp data logs tensorrt_engines

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Warning: Redis is not running. Starting Redis..."
    redis-server --port 6379 --daemonize yes
    sleep 2
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection successful"
else
    echo "❌ Redis connection failed. Please start Redis manually:"
    echo "   redis-server --port 6379"
    exit 1
fi

# Check FFmpeg with NVIDIA codecs
echo "🔍 Checking FFmpeg with NVIDIA codecs..."
if ! ffmpeg -encoders 2>/dev/null | grep -q nvenc; then
    echo "⚠️  Warning: FFmpeg with NVIDIA codecs not found. Video encoding may be slow."
    echo "   Install with: sudo apt-get install nvidia-cuda-toolkit"
fi

# Set environment variables for remote server
export ENV=production
export DEBUG=false
export IS_REMOTE_SERVER=true
export NUM_GPUS=7
export REDIS_HOST=localhost
export REDIS_PORT=6379
export LLAVA_MODEL=llava-hf/LLaVA-NeXT-Video-7B-hf
export WHISPER_MODEL=base
export WINDOW_SECONDS=20
export AUDIO_ENABLED=true

echo "🌐 Starting Remote GPU Server..."
echo "📍 Server will be available at: http://0.0.0.0:8001"
echo "🔧 Production mode: Enabled"
echo "🎮 GPU processing: Enabled"
echo ""

# Start the application
python main.py --mode remote --host 0.0.0.0 --port 8001 