#!/bin/bash

echo "🚀 Starting Ray cluster..."
ray start --head --port=10001 --dashboard-host=0.0.0.0 --dashboard-port=8265

echo "⏳ Waiting for Ray to be ready..."
sleep 3

echo "✅ Starting application..."
export RAY_ADDRESS=localhost:10001
python main.py 