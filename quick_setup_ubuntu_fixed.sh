#!/bin/bash

# AI Video Detective - Quick Ubuntu Setup Script (FIXED VERSION)
# This script automates the complete setup process for Ubuntu server

set -e  # Exit on any error

echo "🚀 AI Video Detective - Quick Ubuntu Setup (FIXED)"
echo "=================================================="
echo "This script will set up the complete environment for AI Video Detective"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root - this is not recommended for security reasons"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: System Update
print_status "Step 1/10: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System packages updated"

# Step 2: Install System Dependencies
print_status "Step 2/10: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
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
    supervisor \
    htop \
    nvtop
print_success "System dependencies installed"

# Step 3: Check NVIDIA Drivers
print_status "Step 3/10: Checking NVIDIA drivers..."
if ! command -v nvidia-smi &> /dev/null; then
    print_error "NVIDIA drivers not found!"
    print_status "Installing NVIDIA drivers..."
    sudo apt install -y nvidia-driver-535
    print_warning "NVIDIA drivers installed. Please reboot and run this script again."
    exit 1
fi
print_success "NVIDIA drivers found"

# Step 4: Check CUDA
print_status "Step 4/10: Checking CUDA installation..."
if ! command -v nvcc &> /dev/null; then
    print_status "CUDA not found. Installing CUDA 12.1..."
    wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
    sudo sh cuda_12.1.0_530.30.02_linux.run --silent --driver --toolkit --samples
    rm cuda_12.1.0_530.30.02_linux.run
    
    # Add CUDA to PATH
    echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
    source ~/.bashrc
fi
print_success "CUDA installation verified"

# Step 5: Install FFmpeg with NVIDIA Support
print_status "Step 5/10: Installing FFmpeg with NVIDIA support..."
sudo apt install -y ffmpeg nvidia-cuda-toolkit
if ffmpeg -encoders 2>/dev/null | grep -q nvenc; then
    print_success "FFmpeg with NVIDIA codecs installed"
else
    print_warning "FFmpeg NVENC support not detected. Video encoding may be slower."
fi

# Step 6: Setup Conda Environment
print_status "Step 6/10: Setting up conda environment..."
# Check if conda is available
if ! command -v conda &> /dev/null; then
    print_error "Conda not found. Please install Miniconda or Anaconda first."
    print_status "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Remove existing environment if it exists
conda env remove -n torch251-cu121 -y 2>/dev/null || true

# Create new conda environment
conda create -n torch251-cu121 python=3.12 -y
conda activate torch251-cu121
pip install --upgrade pip
print_success "Conda environment created"

# Step 7: Install PyTorch with CUDA
print_status "Step 7/10: Installing PyTorch with CUDA support..."
# Install the matched PyTorch trio (WORKING VERSION)
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 \
  --index-url https://download.pytorch.org/whl/cu121
print_success "PyTorch with CUDA installed"

# Step 8: Install Python Dependencies (excluding PyTorch and problematic packages)
print_status "Step 8/10: Installing Python dependencies..."
# Create a temporary requirements file without PyTorch and problematic packages
grep -v "torch\|torchvision\|torchaudio\|--find-links\|bytetrack==0.2.0" requirements_server.txt > requirements_temp.txt
# Also remove ultralytics version constraint for Python 3.12 compatibility
sed -i 's/ultralytics==8.1.28/ultralytics/' requirements_temp.txt
# Remove other problematic version constraints
sed -i 's/supervision==0.18.0/supervision/' requirements_temp.txt
pip install -r requirements_temp.txt
rm requirements_temp.txt
print_success "Python dependencies installed"

# Step 9: Create Directories and Setup
print_status "Step 9/10: Creating directories and configuration..."
mkdir -p static/uploads temp data logs models tensorrt_engines
chmod 755 static/uploads temp data logs

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    print_success "Environment file created from template"
fi

# Step 10: Configure Redis
print_status "Step 10/10: Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is running"
else
    print_error "Redis failed to start"
    exit 1
fi

# Make scripts executable
chmod +x start_remote.sh
chmod +x main.py

print_success "Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate conda environment: conda activate torch251-cu121"
echo "2. Edit .env file: nano .env"
echo "3. Start the server: ./start_remote.sh"
echo "4. Access web interface: http://localhost:8001"
echo ""
echo "🔧 Useful commands:"
echo "- Monitor GPU: watch -n 1 nvidia-smi"
echo "- Check logs: tail -f logs/ai_video_detective_*.log"
echo "- Monitor Redis: redis-cli monitor"
echo "- System resources: htop"
echo ""
echo "📖 For detailed instructions, see: UBUNTU_SETUP_GUIDE.md" 