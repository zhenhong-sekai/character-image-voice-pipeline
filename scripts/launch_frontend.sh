#!/bin/bash

# Character Image Pipeline Frontend Launcher
echo "🎭 Character Image Pipeline Frontend"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "character_image_pipeline.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install requirements
echo "📦 Installing frontend requirements..."
pip3 install -r requirements_frontend.txt

# Start the frontend
echo "🚀 Starting frontend..."
python3 start_frontend.py
