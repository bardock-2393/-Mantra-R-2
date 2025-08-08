# AI Video Detective - Dynamic Troubleshooting Guide

This file will be updated with specific errors and solutions as they are encountered during setup.

## 🚨 Current Issues & Solutions

### No issues reported yet
*Share any error messages you encounter, and I'll add the solutions here with specific commands to run.*

---

## 🔧 Common Setup Issues

### 1. NVIDIA Driver Issues
**Error**: `nvidia-smi: command not found`
**Solution**:
```bash
# Install NVIDIA drivers
sudo apt update
sudo apt install -y nvidia-driver-535
sudo reboot
```

### 2. CUDA Installation Issues
**Error**: `nvcc: command not found`
**Solution**:
```bash
# Download and install CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run --silent --driver --toolkit --samples

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. PyTorch CUDA Issues
**Error**: `CUDA not available in PyTorch` or `No matching distribution found for torch==2.2.0+cu121` or `No matching distribution found for torchvision==0.20.1+cu121`
**Solution** (WORKING):
```bash
# Create new conda environment (recommended)
conda create -n torch251-cu121 python=3.12 -y
conda activate torch251-cu121
pip install --upgrade pip

# Install the matched PyTorch trio (WORKING VERSION)
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 \
  --index-url https://download.pytorch.org/whl/cu121

# Test CUDA
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

**Alternative Solution** (if using venv):
```bash
# Reinstall PyTorch with CUDA support (correct versions)
pip uninstall torch torchvision torchaudio -y
pip install torch==2.5.1+cu121 torchvision==0.21.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121

# Test CUDA
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

### 4. Redis Connection Issues
**Error**: `Redis connection failed`
**Solution**:
```bash
# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping

# If still failing, start manually
redis-server --port 6379 --daemonize yes
```

### 5. Port Already in Use
**Error**: `Address already in use`
**Solution**:
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8001

# Kill the process
sudo kill -9 <PID>

# Or change port
python main.py --mode remote --host 0.0.0.0 --port 8002
```

### 6. Permission Issues
**Error**: `Permission denied`
**Solution**:
```bash
# Make scripts executable
chmod +x *.sh
chmod +x main.py

# Set proper directory permissions
chmod 755 static/uploads temp data logs
```

### 7. Memory Issues
**Error**: `CUDA out of memory`
**Solution**:
```bash
# Set GPU memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Reduce processing load in .env
# Edit .env: TARGET_FPS=30
```

### 8. FFmpeg Issues
**Error**: `FFmpeg NVENC not found`
**Solution**:
```bash
# Install NVIDIA codecs
sudo apt install -y nvidia-cuda-toolkit

# Verify NVENC support
ffmpeg -encoders | grep nvenc
```

---

## 📋 Quick Diagnostic Commands

Run these commands to check your system status:

```bash
# Check system info
echo "=== System Info ==="
uname -a
lsb_release -a

# Check GPU status
echo "=== GPU Status ==="
nvidia-smi

# Check CUDA
echo "=== CUDA Status ==="
nvcc --version
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"

# Check Redis
echo "=== Redis Status ==="
redis-cli ping

# Check disk space
echo "=== Disk Space ==="
df -h

# Check memory
echo "=== Memory ==="
free -h

# Check Python environment
echo "=== Python Environment ==="
which python3
python3 --version
pip list | grep torch
```

---

## 🚀 Quick Fix Commands

### Complete Reset and Setup (Conda - RECOMMENDED)
```bash
# Stop all services
sudo systemctl stop redis-server
sudo pkill -f "python.*main.py"

# Clean and reinstall with conda
conda deactivate
conda env remove -n torch251-cu121 -y
conda create -n torch251-cu121 python=3.12 -y
conda activate torch251-cu121
pip install --upgrade pip

# Install PyTorch trio (WORKING VERSION)
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 \
  --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
pip install -r requirements_server.txt

# Restart services
sudo systemctl start redis-server
./start_remote.sh
```

### Complete Reset and Setup (Venv - Alternative)
```bash
# Stop all services
sudo systemctl stop redis-server
sudo pkill -f "python.*main.py"

# Clean and reinstall
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install torch==2.5.1+cu121 torchvision==0.21.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements_server.txt

# Restart services
sudo systemctl start redis-server
./start_remote.sh
```

### Environment Reset
```bash
# Reset environment file
cp env.example .env

# Edit with basic settings
cat > .env << EOF
ENV=production
DEBUG=false
IS_REMOTE_SERVER=true
NUM_GPUS=1
REDIS_HOST=localhost
REDIS_PORT=6379
LLAVA_MODEL=llava-hf/LLaVA-NeXT-Video-7B-hf
WHISPER_MODEL=base
WINDOW_SECONDS=20
AUDIO_ENABLED=true
EOF
```

---

## 📞 Error Reporting Format

When you encounter an error, please share:

1. **Error message** (exact text)
2. **Command that caused the error**
3. **System info** (run the diagnostic commands above)
4. **What step you were on**

Example:
```
Error: CUDA out of memory
Command: python main.py --mode remote
Step: Starting the application
System: Ubuntu 22.04, 1x RTX 4090, 32GB RAM
```

---

## 🔄 Update Process

1. Share the error with me
2. I'll add the specific solution to this file
3. I'll provide the exact commands to run
4. Test the solution and let me know if it works

---

**Last Updated**: Initial version - ready for error reports 