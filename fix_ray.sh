#!/bin/bash

# Fix Ray configuration issue
echo "🔧 Fixing Ray configuration..."

# Set RAY_ADDRESS to auto to start a new cluster instead of connecting to existing
export RAY_ADDRESS=auto

echo "✅ RAY_ADDRESS set to 'auto'"
echo "🚀 Now try running: python main.py" 