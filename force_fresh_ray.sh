#!/bin/bash

echo "🔧 Force stopping Ray cluster..."
ray stop --force || true

echo "🧹 Killing all Ray processes..."
pkill -9 -f ray || true
pkill -9 -f raylet || true
pkill -9 -f plasma || true

echo "⏳ Waiting for complete cleanup..."
sleep 5

echo "🚀 Starting fresh Ray cluster..."
ray start --head --port=10001 --dashboard-host=0.0.0.0 --dashboard-port=8265

echo "⏳ Waiting for Ray to be ready..."
sleep 5

echo "✅ Starting application..."
export RAY_ADDRESS=localhost:10001
python main.py 