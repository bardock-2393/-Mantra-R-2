#!/bin/bash

echo "🔧 Stopping any existing Ray cluster..."
ray stop || true

echo "🧹 Cleaning up Ray processes..."
pkill -f ray || true

echo "⏳ Waiting for cleanup..."
sleep 3

echo "🚀 Starting new Ray cluster..."
ray start --head --port=10001 --dashboard-host=0.0.0.0 --dashboard-port=8265

echo "⏳ Waiting for Ray cluster to be ready..."
sleep 5

echo "✅ Ray cluster started. Starting application..."
export RAY_ADDRESS=localhost:10001
python main.py 