#!/bin/bash

# Character Image Pipeline - Simple Gradio Launcher
echo "🎭 Character Image Pipeline - Gradio Frontend"
echo "============================================="

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

# Check if API server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is already running on port 8000"
else
    echo "🚀 Starting API server..."
    python3 api_server.py &
    API_PID=$!
    
    # Wait for API server to start
    echo "⏳ Waiting for API server to start..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API server started successfully!"
            break
        fi
        echo "⏳ Waiting... ($i/10)"
        sleep 2
    done
    
    # Check if API server started
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "❌ API server failed to start"
        exit 1
    fi
fi

# Install Gradio if needed
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "📦 Installing Gradio..."
    pip3 install gradio
fi

# Start Gradio frontend
echo "🎭 Starting Gradio frontend..."
echo "🌐 Frontend will be available at: http://localhost:7860"
echo "🔧 API server running at: http://localhost:8000"
echo ""

python3 gradio_app.py
