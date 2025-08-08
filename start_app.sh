#!/bin/bash

echo "🚀 AI Video Detective - Complete Startup Script"
echo "================================================"

# Stop any existing Ray cluster
echo "🔧 Stopping any existing Ray cluster..."
ray stop --force || true

# Kill any remaining Ray processes
echo "🧹 Cleaning up Ray processes..."
pkill -9 -f ray || true
pkill -9 -f raylet || true
pkill -9 -f plasma || true

# Wait for cleanup
echo "⏳ Waiting for cleanup..."
sleep 5

# Start fresh Ray cluster
echo "🚀 Starting fresh Ray cluster..."
ray start --head --port=10001 --dashboard-host=0.0.0.0 --dashboard-port=8265

# Wait for Ray to be ready
echo "⏳ Waiting for Ray cluster to be ready..."
sleep 10

# Check if Ray is running
echo "🔍 Checking Ray cluster status..."
if ray status > /dev/null 2>&1; then
    echo "✅ Ray cluster is running"
else
    echo "❌ Ray cluster failed to start"
    exit 1
fi

# Set environment variable
export RAY_ADDRESS=localhost:10001

# Start the application
echo "🎯 Starting AI Video Detective application..."
python main.py 