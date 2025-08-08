#!/bin/bash

echo "🔧 Fixing torchaudio compatibility issue..."

echo "📦 Uninstalling current torchaudio..."
pip uninstall torchaudio -y

echo "📦 Installing torchaudio with correct CUDA version..."
pip install torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121

echo "✅ Torchaudio fixed!"
echo "🚀 Now try running: python main.py" 