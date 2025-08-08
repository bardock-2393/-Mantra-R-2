@echo off
REM AI Video Detective - Fallback Mode Startup Script
REM This script starts the application without VLM to avoid compatibility issues

echo === AI Video Detective - Fallback Mode ===

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the ai_video_detective2 directory.
    pause
    exit /b 1
)

REM Load environment variables from server.env
if exist "server.env" (
    echo Loading environment variables from server.env...
    for /f "tokens=1,2 delims==" %%a in (server.env) do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
            echo   %%a=%%b
        )
    )
) else (
    echo Warning: server.env not found, using default values
)

REM Set environment variables for fallback mode
set RAY_NUM_CPUS=2
set RAY_NUM_GPUS=0
set RAY_OBJECT_STORE_MEMORY=500000000
set ENV=production
set DEBUG=false
set IS_REMOTE_SERVER=true
set DISABLE_VLM=true
set USE_FALLBACK_MODE=true

echo Environment variables set for fallback mode:
echo   RAY_NUM_CPUS=%RAY_NUM_CPUS%
echo   RAY_NUM_GPUS=%RAY_NUM_GPUS%
echo   DISABLE_VLM=%DISABLE_VLM%
echo   USE_FALLBACK_MODE=%USE_FALLBACK_MODE%

REM Check if Python virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install basic packages (skip VLM dependencies)
echo Installing basic packages...
python -m pip install --upgrade pip
pip install Flask Flask-SocketIO Flask-CORS redis duckdb pandas numpy psutil python-dotenv

REM Create necessary directories
echo Creating necessary directories...
if not exist "static\uploads" mkdir static\uploads
if not exist "temp" mkdir temp
if not exist "data" mkdir data

REM Start the application
echo Starting AI Video Detective in fallback mode...
echo VLM capabilities disabled to avoid compatibility issues
echo Access the application at: http://localhost:8888
echo Press Ctrl+C to stop

python app.py

pause 