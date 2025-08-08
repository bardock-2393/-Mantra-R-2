#!/bin/bash

echo "🚀 AI Video Detective - Complete Server Setup"
echo "=============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root - this is not recommended for security reasons"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    cmake \
    pkg-config \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    redis-server \
    nginx \
    supervisor

# Check NVIDIA drivers and CUDA
echo "🔍 Checking NVIDIA drivers and CUDA..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ Error: NVIDIA drivers not found."
    echo "Please install NVIDIA drivers first:"
    echo "https://docs.nvidia.com/cuda/cuda-installation-guide-linux/"
    exit 1
fi

if ! command -v nvcc &> /dev/null; then
    echo "❌ Error: CUDA toolkit not found."
    echo "Please install CUDA toolkit first:"
    echo "https://developer.nvidia.com/cuda-downloads"
    exit 1
fi

# Check FFmpeg with NV codecs
echo "🎬 Checking FFmpeg with NV codecs..."
if ! command -v ffmpeg &> /dev/null; then
    echo "📹 Installing FFmpeg with NV codecs..."
    sudo apt install -y ffmpeg
fi

# Check if FFmpeg supports NV codecs
if ! ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_nvenc"; then
    echo "⚠️  Warning: FFmpeg NVENC support not detected. Video encoding may be slower."
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA support first
echo "🔥 Installing PyTorch with CUDA 12.1 support..."
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements_server.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/uploads temp data logs models

# Set up Redis
echo "🔴 Setting up Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis connection
if ! redis-cli ping &> /dev/null; then
    echo "❌ Error: Redis is not running properly."
    exit 1
fi

# Set up environment variables
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
fi

# Set proper permissions
echo "🔐 Setting proper permissions..."
chmod +x start_remote.sh
chmod +x main.py

# Create systemd service (optional)
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/ai-video-detective.service > /dev/null <<EOF
[Unit]
Description=AI Video Detective
After=network.target redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py --mode remote --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-video-detective.service

echo "✅ Server setup completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your specific configuration"
echo "2. Start the service: sudo systemctl start ai-video-detective"
echo "3. Check status: sudo systemctl status ai-video-detective"
echo "4. View logs: sudo journalctl -u ai-video-detective -f"
echo ""
echo "🚀 Or run manually: ./start_remote.sh"
echo ""
echo "📊 Monitor GPU usage: watch -n 1 nvidia-smi"
echo "🔍 Check Redis: redis-cli monitor" 