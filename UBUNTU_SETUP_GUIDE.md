# AI Video Detective - Ubuntu Server Setup Guide

This guide provides step-by-step instructions to set up and run the AI Video Detective application on Ubuntu server.

## 🎯 Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS (recommended)
- **RAM**: 64GB+ (128GB recommended for 7× A100 setup)
- **Storage**: 1TB+ SSD
- **GPU**: 7× NVIDIA A100 80GB (or equivalent)
- **CPU**: 16+ cores recommended

### Software Requirements
- Python 3.10+
- CUDA 12.1+
- NVIDIA drivers 535+
- FFmpeg with NVIDIA codecs
- Redis 6.0+

## 🚀 Step-by-Step Setup

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
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
```

### Step 2: NVIDIA Driver Installation

```bash
# Check if NVIDIA drivers are already installed
nvidia-smi

# If not installed, install NVIDIA drivers
sudo apt install -y nvidia-driver-535

# Install CUDA toolkit
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

# Add CUDA to PATH
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify installation
nvcc --version
nvidia-smi
```

### Step 3: FFmpeg with NVIDIA Codecs

```bash
# Install FFmpeg with NVIDIA support
sudo apt install -y ffmpeg

# Install NVIDIA CUDA toolkit for codecs
sudo apt install -y nvidia-cuda-toolkit

# Verify NVENC support
ffmpeg -encoders | grep nvenc
```

### Step 4: Clone and Setup Project

```bash
# Clone the repository (if not already done)
git clone <your-repository-url>
cd ai_video_detective2

# Make setup script executable
chmod +x setup_server.sh
chmod +x start_remote.sh

# Run the automated setup
./setup_server.sh
```

### Step 5: Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit the environment file
nano .env
```

**Key environment variables to configure:**

```bash
# Set to true for GPU server
IS_REMOTE_SERVER=true

# Configure GPU settings
NUM_GPUS=7
GPU_MEMORY_GB=80

# Set server URL
REMOTE_GPU_SERVER_URL=http://your-server-ip:8001

# Configure Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Set production mode
ENV=production
DEBUG=false
```

### Step 6: Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
pip install -r requirements_server.txt
```

### Step 7: Directory Setup

```bash
# Create necessary directories
mkdir -p static/uploads temp data logs models tensorrt_engines

# Set proper permissions
chmod 755 static/uploads temp data logs
```

### Step 8: Redis Configuration

```bash
# Start Redis service
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis connection
redis-cli ping

# Configure Redis for production (optional)
sudo nano /etc/redis/redis.conf
```

**Add to redis.conf:**
```
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Step 9: Test GPU Setup

```bash
# Test CUDA availability
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"

# Test GPU memory
nvidia-smi

# Test FFmpeg with NVIDIA codecs
ffmpeg -f lavfi -i testsrc=duration=1:size=1280x720:rate=1 -c:v h264_nvenc -y test.mp4
```

### Step 10: Start the Application

#### Option A: Manual Start
```bash
# Activate virtual environment
source venv/bin/activate

# Start the remote GPU server
python main.py --mode remote --host 0.0.0.0 --port 8001
```

#### Option B: Using Startup Script
```bash
# Use the provided startup script
./start_remote.sh
```

#### Option C: Systemd Service (Recommended for Production)
```bash
# The setup script should have created the service
# Start the service
sudo systemctl start ai-video-detective

# Enable auto-start on boot
sudo systemctl enable ai-video-detective

# Check status
sudo systemctl status ai-video-detective

# View logs
sudo journalctl -u ai-video-detective -f
```

## 🔧 Configuration Options

### GPU Allocation
The system is designed for 7× A100 GPUs:
- **GPU 0-3**: Video processing (RT-DETR-v2, ByteTrack)
- **GPU 4**: Audio processing (Whisper, Wav2Vec2)
- **GPU 5**: VLM serving (LLaVA-NeXT-Video-7B)
- **GPU 6**: Video encoding (NVENC)

### For Different GPU Configurations

#### Single GPU Setup
```bash
# Edit .env
NUM_GPUS=1
LLAVA_DEVICE=cuda:0
DETECTION_DEVICE=cuda:0
```

#### Multi-GPU Setup (Less than 7)
```bash
# Edit .env
NUM_GPUS=4  # Adjust based on your setup
LLAVA_DEVICE=cuda:3
DETECTION_DEVICE=cuda:0
```

## 🚀 Running the Application

### 1. Start the Server
```bash
# Production mode
python main.py --mode remote --host 0.0.0.0 --port 8001

# Development mode with debug
python main.py --mode remote --host 0.0.0.0 --port 8001 --debug
```

### 2. Access the Web Interface
- **Local**: http://localhost:8001
- **Remote**: http://your-server-ip:8001

### 3. Monitor the System
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor Redis
redis-cli monitor

# Monitor logs
tail -f logs/ai_video_detective_*.log

# Monitor system resources
htop
```

## 🔍 Troubleshooting

### Common Issues

#### 1. CUDA Not Available
```bash
# Check CUDA installation
nvcc --version
nvidia-smi

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
```

#### 2. GPU Memory Errors
```bash
# Set GPU memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Reduce batch size in config
# Edit .env: TARGET_FPS=30
```

#### 3. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis-server

# Start Redis manually
redis-server --port 6379

# Test connection
redis-cli ping
```

#### 4. FFmpeg NVENC Issues
```bash
# Install NVIDIA codecs
sudo apt install -y nvidia-cuda-toolkit

# Verify NVENC support
ffmpeg -encoders | grep nvenc
```

#### 5. Port Already in Use
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8001

# Kill the process or change port
python main.py --mode remote --host 0.0.0.0 --port 8002
```

### Performance Optimization

#### 1. GPU Memory Optimization
```bash
# Set environment variables
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### 2. System Optimization
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize Redis
sudo nano /etc/redis/redis.conf
# Add: maxmemory 4gb
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check application health
curl http://localhost:8001/health

# Check GPU status
nvidia-smi

# Check Redis
redis-cli ping

# Check disk space
df -h

# Check memory usage
free -h
```

### Log Management
```bash
# View application logs
tail -f logs/ai_video_detective_*.log

# Rotate logs (add to crontab)
0 0 * * * find /path/to/logs -name "*.log" -mtime +7 -delete
```

### Backup Strategy
```bash
# Backup configuration
cp .env .env.backup

# Backup data
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# Backup models (if downloaded locally)
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
```

## 🎯 Next Steps

1. **Test with Sample Video**: Upload a test video to verify functionality
2. **Configure Analysis Types**: Customize analysis parameters in `.env`
3. **Set Up Monitoring**: Configure system monitoring and alerting
4. **Security Hardening**: Configure firewall, SSL certificates, and access controls
5. **Performance Tuning**: Optimize based on your specific hardware and requirements

## 📞 Support

- Check logs: `tail -f logs/ai_video_detective_*.log`
- Monitor GPU: `watch -n 1 nvidia-smi`
- Check Redis: `redis-cli monitor`
- System status: `sudo systemctl status ai-video-detective`

---

**AI Video Detective** - Advanced Multi-Modal Video Analysis with Real-time AI 