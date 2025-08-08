#!/bin/bash

# AI Video Detective - System Diagnostic Script
# Run this when you encounter errors to collect system information

echo "🔍 AI Video Detective - System Diagnostic Report"
echo "================================================"
echo "Date: $(date)"
echo ""

# System Information
echo "📋 SYSTEM INFORMATION"
echo "===================="
echo "OS: $(uname -a)"
echo "Distribution: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo ""

# GPU Information
echo "🎮 GPU INFORMATION"
echo "================="
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA-SMI found:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo ""
    echo "GPU Details:"
    nvidia-smi
else
    echo "❌ NVIDIA-SMI not found"
fi
echo ""

# CUDA Information
echo "🔥 CUDA INFORMATION"
echo "=================="
if command -v nvcc &> /dev/null; then
    echo "CUDA Version: $(nvcc --version | grep release | cut -d' ' -f6)"
else
    echo "❌ CUDA not found"
fi
echo ""

# Python Environment
echo "🐍 PYTHON ENVIRONMENT"
echo "===================="
echo "Python Version: $(python3 --version)"
echo "Python Path: $(which python3)"
echo "Pip Version: $(pip --version)"
echo ""

# PyTorch Information
echo "🔥 PYTORCH INFORMATION"
echo "====================="
if python3 -c "import torch; print(f'PyTorch Version: {torch.__version__}')" 2>/dev/null; then
    python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
    python3 -c "import torch; print(f'CUDA Version: {torch.version.cuda}')"
    python3 -c "import torch; print(f'GPU Count: {torch.cuda.device_count()}')"
    if torch.cuda.is_available(); then
        python3 -c "import torch; print(f'Current GPU: {torch.cuda.get_device_name(0)}')"
    fi
else
    echo "❌ PyTorch not installed"
fi
echo ""

# Redis Information
echo "🔴 REDIS INFORMATION"
echo "==================="
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
        echo "Redis Version: $(redis-cli --version)"
    else
        echo "❌ Redis is not responding"
    fi
else
    echo "❌ Redis CLI not found"
fi
echo ""

# FFmpeg Information
echo "🎬 FFMPEG INFORMATION"
echo "===================="
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg Version: $(ffmpeg -version | head -n1)"
    if ffmpeg -encoders 2>/dev/null | grep -q nvenc; then
        echo "✅ NVENC support available"
    else
        echo "❌ NVENC support not found"
    fi
else
    echo "❌ FFmpeg not found"
fi
echo ""

# Disk Space
echo "💾 DISK SPACE"
echo "============="
df -h
echo ""

# Memory Information
echo "🧠 MEMORY INFORMATION"
echo "===================="
free -h
echo ""

# Network Information
echo "🌐 NETWORK INFORMATION"
echo "====================="
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I)"
echo ""

# Process Information
echo "⚙️ RUNNING PROCESSES"
echo "==================="
echo "Python processes:"
ps aux | grep python | grep -v grep
echo ""
echo "Redis processes:"
ps aux | grep redis | grep -v grep
echo ""

# Environment Variables
echo "🔧 ENVIRONMENT VARIABLES"
echo "======================="
echo "PATH: $PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "CUDA_HOME: $CUDA_HOME"
echo ""

# Virtual Environment
echo "🐍 VIRTUAL ENVIRONMENT"
echo "====================="
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "❌ No virtual environment active"
fi
echo ""

# Installed Packages
echo "📦 INSTALLED PACKAGES"
echo "===================="
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Key packages in virtual environment:"
    pip list | grep -E "(torch|transformers|opencv|redis|flask)"
else
    echo "No virtual environment active"
fi
echo ""

echo "📄 DIAGNOSTIC COMPLETE"
echo "====================="
echo "Copy the output above and share it with me when reporting errors."
echo "Also include:"
echo "1. The exact error message"
echo "2. The command that caused the error"
echo "3. What step you were on" 