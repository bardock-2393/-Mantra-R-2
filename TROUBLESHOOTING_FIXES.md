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

### 4. Server Mode Configuration
**Problem**: Application trying to forward to non-existent remote server

**Fix**: Updated video processing logic to handle local processing when running on a server.

## How to Use the Fixes

### Option 1: Use the Server Startup Script (Recommended for Server)

**Windows Server:**
```cmd
cd ai_video_detective2
start_server.bat
```

**Linux/Mac Server:**
```bash
cd ai_video_detective2
chmod +x start_server.sh
./start_server.sh
```

### Option 2: Use the Fixed Startup Script (For Development)

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

### Option 3: Manual Server Configuration

1. **Set Server Environment Variables:**
   ```cmd
   set IS_REMOTE_SERVER=true
   set RAY_NUM_CPUS=2
   set RAY_NUM_GPUS=0
   set RAY_OBJECT_STORE_MEMORY=500000000
   set ENV=production
   set DEBUG=false
   ```

2. **Fix Ray Cluster:**
   ```bash
   python fix_ray_resources.py
   ```

3. **Start Application:**
   ```bash
   python app.py
   ```

## Environment Variables Explained

### Server Mode (Everything Local)
- `IS_REMOTE_SERVER=true`: Processes videos locally on the server
- `RAY_NUM_CPUS=2`: Uses only 2 CPU cores (conservative)
- `RAY_NUM_GPUS=0`: No GPU usage (CPU-only processing)
- `RAY_OBJECT_STORE_MEMORY=500000000`: 500MB object store
- `ENV=production`: Production mode
- `DEBUG=false`: Disable debug mode

### Development Mode (Local + Remote)
- `IS_REMOTE_SERVER=false`: Forwards to remote GPU server
- `RAY_NUM_CPUS=4`: More CPU cores for development
- `RAY_NUM_GPUS=1`: GPU usage for development
- `ENV=development`: Development mode
- `DEBUG=true`: Enable debug mode

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
5. **Video Processing**: Should process locally on the server

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
- Ensure you're using the server startup script (`start_server.bat`)
- Check that `IS_REMOTE_SERVER=true` is set
- Verify the application logs for specific error messages

### For Server Deployment:
- Use `start_server.bat` or set `IS_REMOTE_SERVER=true`
- Set `RAY_NUM_GPUS=0` if no GPU is available
- Use `ENV=production` for better performance

## Support

If you continue to experience issues after applying these fixes, please:
1. Run `python fix_ray_resources.py` and share the output
2. Check the application logs for specific error messages
3. Verify your system meets the minimum requirements
4. Confirm you're using the correct startup script for your environment 