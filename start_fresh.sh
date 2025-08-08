#!/bin/bash

echo "🔧 Stopping any existing Ray cluster..."
ray stop || true

echo "🧹 Cleaning up Ray processes..."
pkill -f ray || true

echo "⏳ Waiting for cleanup..."
sleep 2

echo "🚀 Starting application with fresh Ray cluster..."
export RAY_ADDRESS=auto
python main.py 