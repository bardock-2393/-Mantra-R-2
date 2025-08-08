# AI Video Detective - Troubleshooting Fixes

This document explains the fixes implemented for the common issues you're experiencing.

## Issues Fixed

### 1. Socket.IO CORS Error
**Problem**: `http://localhost:8888 is not an accepted origin`

**Fix**: Updated `config.py` to include specific localhost origins in CORS configuration:
```python
self.cors_origins = [
    "*",
    "http://localhost:8888",
    "http://localhost:8080", 
    "http://localhost:8000",
    "http://127.0.0.1:8888",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000"
]
```

### 2. API Endpoint 405 Error
**Problem**: `405 Client Error: Not Allowed for url: http://localhost:8001/api/process_video`

**Fix**: Added the missing `/api/process_video` endpoint in `app.py` that handles video processing requests from local servers.

### 3. Ray Cluster Resource Exhaustion
**Problem**: `all cluster resources being claimed by actors`

**Fix**: Created `fix_ray_resources.py` script that:
- Monitors system resources
- Optimizes Ray configuration based on available resources
- Cleans up existing actors
- Restarts cluster with conservative resource allocation

## How to Use the Fixes

### Option 1: Use the Fixed Startup Script (Recommended)

**Windows:**
```cmd
cd ai_video_detective2
start_fixed.bat
```

**Linux/Mac:**
```bash
cd ai_video_detective2
chmod +x start_fixed.sh
./start_fixed.sh
```

### Option 2: Manual Fix

1. **Fix Ray Cluster:**
   ```bash
   python fix_ray_resources.py
   ```

2. **Set Environment Variables:**
   ```bash
   export RAY_NUM_CPUS=4
   export RAY_NUM_GPUS=1
   export RAY_OBJECT_STORE_MEMORY=500000000
   export IS_REMOTE_SERVER=false
   ```

3. **Start Application:**
   ```bash
   python app.py
   ```

## Environment Variables Explained

- `RAY_NUM_CPUS=4`: Limits Ray to use only 4 CPU cores (prevents exhaustion)
- `RAY_NUM_GPUS=1`: Limits Ray to use only 1 GPU (prevents GPU exhaustion)
- `RAY_OBJECT_STORE_MEMORY=500000000`: Limits object store to 500MB (prevents memory issues)
- `IS_REMOTE_SERVER=false`: Runs in local mode (no remote GPU server needed)

## Monitoring and Maintenance

### Check Ray Cluster Health
```bash
python fix_ray_resources.py
```

### Monitor System Resources
The script will show:
- CPU usage and count
- Memory usage and total
- GPU count and availability
- Ray cluster status

### Restart Ray Cluster
If you encounter resource issues again:
```bash
python fix_ray_resources.py
```

## Expected Behavior After Fixes

1. **Socket.IO**: Should connect without CORS errors
2. **Video Upload**: Should work without 405 errors
3. **Ray Cluster**: Should start with optimized resources
4. **Application**: Should be accessible at http://localhost:8888

## Troubleshooting

### If Socket.IO still fails:
- Check browser console for specific CORS errors
- Ensure you're accessing via http://localhost:8888 (not https)
- Clear browser cache and reload

### If Ray still has resource issues:
- Run `python fix_ray_resources.py` to restart cluster
- Check system resource usage with Task Manager/htop
- Consider reducing `RAY_NUM_CPUS` or `RAY_NUM_GPUS` further

### If video upload still fails:
- Check if the remote server (port 8001) is running
- Verify the `/api/process_video` endpoint is accessible
- Check application logs for specific error messages

## Support

If you continue to experience issues after applying these fixes, please:
1. Run `python fix_ray_resources.py` and share the output
2. Check the application logs for specific error messages
3. Verify your system meets the minimum requirements 