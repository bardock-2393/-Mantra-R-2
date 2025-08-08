# AI Video Detective - Ubuntu Setup Checklist

## ✅ Quick Setup (Automated)

1. **Make script executable and run:**
   ```bash
   chmod +x quick_setup_ubuntu.sh
   ./quick_setup_ubuntu.sh
   ```

2. **Configure environment:**
   ```bash
   nano .env
   # Set IS_REMOTE_SERVER=true
   # Set NUM_GPUS=7 (or your GPU count)
   # Set ENV=production
   ```

3. **Start the server:**
   ```bash
   ./start_remote.sh
   ```

4. **Access web interface:**
   - Open browser: http://localhost:8001

## ✅ Manual Setup (Step by Step)

### Prerequisites Check
- [ ] Ubuntu 22.04 LTS
- [ ] NVIDIA GPU with drivers
- [ ] 64GB+ RAM
- [ ] 1TB+ storage

### System Setup
- [ ] Update system: `sudo apt update && sudo apt upgrade -y`
- [ ] Install dependencies: `sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential redis-server ffmpeg`
- [ ] Install NVIDIA drivers: `sudo apt install -y nvidia-driver-535`
- [ ] Install CUDA 12.1: Download from NVIDIA website
- [ ] Verify GPU: `nvidia-smi`
- [ ] Verify CUDA: `nvcc --version`

### Project Setup
- [ ] Clone repository: `git clone <repo-url> && cd ai_video_detective2`
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Activate environment: `source venv/bin/activate`
- [ ] Install PyTorch: `pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121`
- [ ] Install dependencies: `pip install -r requirements_server.txt`
- [ ] Create directories: `mkdir -p static/uploads temp data logs models`
- [ ] Copy environment: `cp env.example .env`

### Configuration
- [ ] Edit .env file: `nano .env`
- [ ] Set IS_REMOTE_SERVER=true
- [ ] Set NUM_GPUS=7 (or your count)
- [ ] Set ENV=production
- [ ] Configure Redis settings

### Services
- [ ] Start Redis: `sudo systemctl start redis-server`
- [ ] Test Redis: `redis-cli ping`
- [ ] Make scripts executable: `chmod +x start_remote.sh`

### Testing
- [ ] Test CUDA: `python3 -c "import torch; print(torch.cuda.is_available())"`
- [ ] Test GPU count: `python3 -c "import torch; print(torch.cuda.device_count())"`
- [ ] Test FFmpeg: `ffmpeg -encoders | grep nvenc`

### Start Application
- [ ] Start server: `./start_remote.sh`
- [ ] Check logs: `tail -f logs/ai_video_detective_*.log`
- [ ] Monitor GPU: `watch -n 1 nvidia-smi`
- [ ] Access web UI: http://localhost:8001

## 🔧 Troubleshooting

### Common Issues
- **CUDA not available**: Reinstall PyTorch with CUDA support
- **GPU memory errors**: Reduce TARGET_FPS in .env
- **Redis connection failed**: Start Redis service
- **Port in use**: Change port or kill existing process
- **FFmpeg NVENC missing**: Install nvidia-cuda-toolkit

### Performance Tuning
- Set GPU memory optimization: `export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512`
- Optimize Redis: Add `maxmemory 4gb` to redis.conf
- Increase file limits: Add to /etc/security/limits.conf

## 📊 Monitoring

### Health Checks
- Application: `curl http://localhost:8001/health`
- GPU: `nvidia-smi`
- Redis: `redis-cli ping`
- System: `htop`

### Logs
- Application: `tail -f logs/ai_video_detective_*.log`
- System: `sudo journalctl -u ai-video-detective -f`

## 🎯 Success Criteria

- [ ] Web interface accessible at http://localhost:8001
- [ ] GPU utilization visible in nvidia-smi
- [ ] Redis connection successful
- [ ] Video upload and processing working
- [ ] AI analysis responding to queries

## 📞 Support

- Check logs: `tail -f logs/ai_video_detective_*.log`
- Monitor GPU: `watch -n 1 nvidia-smi`
- Check Redis: `redis-cli monitor`
- System status: `sudo systemctl status ai-video-detective` 