#!/usr/bin/env python3
"""
Startup script for the Character Image Pipeline Frontend
Runs both API server and Streamlit app
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def install_requirements():
    """Install frontend requirements"""
    print("📦 Installing frontend requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_frontend.txt"], check=True)
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    try:
        # Start API server in background
        api_process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully!")
                return api_process
        except:
            print("❌ API server failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_streamlit():
    """Start the Streamlit app"""
    print("🎭 Starting Streamlit app...")
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

def main():
    print("🎭 Character Image Pipeline Frontend")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("character_image_pipeline.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot start without API server")
        sys.exit(1)
    
    try:
        # Start Streamlit
        start_streamlit()
    finally:
        # Cleanup
        if api_process:
            print("🛑 Stopping API server...")
            api_process.terminate()
            api_process.wait()

if __name__ == "__main__":
    main()
