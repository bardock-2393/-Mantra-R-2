@echo off
REM AI Video Detective - Server Startup Script
REM This script starts the application in server mode (everything local)

echo === AI Video Detective - Server Mode ===

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the ai_video_detective2 directory.
    pause
    exit /b 1
)

REM Set environment variables for server mode
set RAY_NUM_CPUS=2
set RAY_NUM_GPUS=0
set RAY_OBJECT_STORE_MEMORY=500000000
set ENV=production
set DEBUG=false
set IS_REMOTE_SERVER=true
set REMOTE_GPU_SERVER_URL=http://localhost:8001

echo Environment variables set for server mode:
echo   RAY_NUM_CPUS=%RAY_NUM_CPUS%
echo   RAY_NUM_GPUS=%RAY_NUM_GPUS%
echo   RAY_OBJECT_STORE_MEMORY=%RAY_OBJECT_STORE_MEMORY%
echo   IS_REMOTE_SERVER=%IS_REMOTE_SERVER%
echo   ENV=%ENV%

REM Check if Python virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade required packages
echo Installing/upgrade packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Fix Ray cluster issues
echo Fixing Ray cluster issues...
python fix_ray_resources.py

REM Create necessary directories
echo Creating necessary directories...
if not exist "static\uploads" mkdir static\uploads
if not exist "temp" mkdir temp
if not exist "data" mkdir data

REM Start the application
echo Starting AI Video Detective in server mode...
echo Access the application at: http://localhost:8888
echo Press Ctrl+C to stop

python app.py

pause 