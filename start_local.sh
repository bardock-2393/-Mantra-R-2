#!/bin/bash

# AI Video Detective - Local Development Server Startup Script

echo "🚀 Starting AI Video Detective - Local Development Server"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/uploads temp data logs

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Warning: Redis is not running. Starting Redis..."
    redis-server --port 6379 --daemonize yes
    sleep 2
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection successful"
else
    echo "❌ Redis connection failed. Please start Redis manually:"
    echo "   redis-server --port 6379"
    exit 1
fi

# Set environment variables
export ENV=development
export DEBUG=true
export IS_REMOTE_SERVER=false
export REDIS_HOST=localhost
export REDIS_PORT=6379

echo "🌐 Starting Flask development server..."
echo "📍 Server will be available at: http://localhost:8888"
echo "🔧 Debug mode: Enabled"
echo ""

# Start the application
python main.py --mode local --debug --host 0.0.0.0 --port 8888 