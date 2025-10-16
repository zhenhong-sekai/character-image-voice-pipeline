#!/usr/bin/env python3
"""
Launch script for Gradio frontend with real-time progress
"""

import subprocess
import sys
import time
import requests
import os

def check_api_server():
    """Check if API server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """Start API server if not running"""
    if check_api_server():
        print("✅ API server already running")
        return True
    
    print("🚀 Starting API server...")
    try:
        # Start API server in background
        api_process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for i in range(10):
            time.sleep(1)
            if check_api_server():
                print("✅ API server started successfully!")
                return True
            print(f"⏳ Waiting for API server... ({i+1}/10)")
        
        print("❌ API server failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return False

def install_gradio():
    """Install Gradio if not available"""
    try:
        import gradio as gr
        print("✅ Gradio already installed")
        return True
    except ImportError:
        print("📦 Installing Gradio...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "gradio"], check=True)
            print("✅ Gradio installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Gradio: {e}")
            return False

def main():
    print("🎭 Character Image Pipeline - Gradio Frontend")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("character_image_pipeline.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install Gradio
    if not install_gradio():
        sys.exit(1)
    
    # Start API server
    if not start_api_server():
        sys.exit(1)
    
    # Launch Gradio app
    print("🎭 Starting Gradio frontend...")
    print("🌐 Frontend will be available at: http://localhost:7860")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        import gradio as gr
        from gradio_app import create_interface
        
        demo = create_interface()
        demo.queue().launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start Gradio: {e}")

if __name__ == "__main__":
    main()
