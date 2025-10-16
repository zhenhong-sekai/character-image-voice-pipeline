#!/bin/bash

# Character Image Pipeline - Gradio Frontend Launcher
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

# Install requirements if needed
echo "📦 Checking requirements..."
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "📦 Installing Gradio..."
    pip3 install gradio
fi

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing FastAPI..."
    pip3 install fastapi uvicorn python-multipart
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ ! -z "$API_PID" ]; then
        echo "🛑 Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$GRADIO_PID" ]; then
        echo "🛑 Stopping Gradio frontend (PID: $GRADIO_PID)..."
        kill $GRADIO_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start API server in background
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

# Check if API server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API server failed to start"
    cleanup
    exit 1
fi

# Start Gradio frontend
echo "🎭 Starting Gradio frontend..."
echo "🌐 Frontend will be available at: http://localhost:7860"
echo "🔧 API server running at: http://localhost:8000"
echo "🛑 Press Ctrl+C to stop both services"
echo ""

python3 gradio_app.py &
GRADIO_PID=$!

# Wait for Gradio to start
sleep 3

# Check if Gradio is running
if ! curl -s http://localhost:7860 > /dev/null 2>&1; then
    echo "⏳ Gradio is starting up..."
    sleep 5
fi

echo "✅ Both services are running!"
echo "🎭 Gradio Frontend: http://localhost:7860"
echo "🔧 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Keep script running and wait for interrupt
wait
