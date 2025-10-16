#!/usr/bin/env python3
"""
Streamlit Frontend for Character Image Pipeline
Real-time progress tracking and beautiful UI
"""

import streamlit as st
import requests
import time
import os
import json
from datetime import datetime
from PIL import Image
import io
import base64

# Page config
st.set_page_config(
    page_title="🎭 Character Image Pipeline",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .step-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    
    .progress-container {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .status-success {
        color: #00ff00;
        font-weight: bold;
    }
    
    .status-error {
        color: #ff0000;
        font-weight: bold;
    }
    
    .status-processing {
        color: #ffa500;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def check_api_connection():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_image_to_api(uploaded_file):
    """Upload image to API server"""
    try:
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def analyze_image_with_api(file_path):
    """Analyze image using API"""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json={"file_path": file_path})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analysis failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def start_pipeline(use_google_search=False, character_name=None, max_candidates=5):
    """Start the pipeline"""
    try:
        payload = {
            "use_google_search": use_google_search,
            "character_name": character_name,
            "max_candidates": max_candidates
        }
        response = requests.post(f"{API_BASE_URL}/process", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Pipeline start failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Pipeline start error: {str(e)}")
        return None

def get_job_status(job_id):
    """Get job status from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def display_progress_bar(progress, current_step, message):
    """Display progress bar with step information"""
    st.markdown(f"""
    <div class="progress-container">
        <h4>🔄 {current_step}</h4>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress / 100)
    st.write(f"Progress: {progress}%")

def display_analysis_results(analysis):
    """Display analysis results in a nice format"""
    if not analysis:
        return
    
    st.markdown("### 📊 Image Analysis Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Quality & Detection")
        st.write(f"**Quality:** {'✅ Good' if analysis['quality']['is_ok'] else '❌ Poor'}")
        st.write(f"**Persons:** {analysis['person_count']}")
        st.write(f"**Faces:** {analysis['face_count']}")
        st.write(f"**Composition:** {analysis['composition']}")
    
    with col2:
        st.markdown("#### 🎭 Cowboy Shot Analysis")
        cowboy = analysis['cowboy_analysis']
        st.write(f"**Status:** {cowboy['reason']}")
        st.write(f"**Needs Outpainting:** {'Yes' if cowboy['needs_outpainting'] else 'No'}")
        if cowboy['needs_outpainting']:
            st.write(f"**Strategy:** {cowboy['strategy']}")
            st.write(f"**Prompt:** {cowboy['prompt']}")

def main():
    # Header
    st.markdown('<h1 class="main-header">🎭 Character Image Pipeline</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Check API connection
    if not check_api_connection():
        st.error("❌ Cannot connect to API server. Please make sure the API server is running on localhost:8000")
        st.info("Run: `python api_server.py` to start the API server")
        return
    
    st.success("✅ Connected to API server")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Pipeline Controls")
        
        # Pipeline settings
        st.markdown("### Settings")
        use_google_search = st.checkbox("Use Google Search", value=False)
        character_name = st.text_input("Character Name", value="") if use_google_search else None
        max_candidates = st.slider("Max Candidates", 1, 10, 5)
        
        st.markdown("---")
        
        # Job management
        st.markdown("### Job Management")
        if st.button("🔄 Refresh Jobs"):
            st.rerun()
        
        # Display active jobs
        try:
            jobs_response = requests.get(f"{API_BASE_URL}/jobs")
            if jobs_response.status_code == 200:
                jobs = jobs_response.json()["jobs"]
                if jobs:
                    st.markdown("#### Active Jobs")
                    for job_id in jobs:
                        st.write(f"Job: {job_id[:8]}...")
                else:
                    st.write("No active jobs")
        except:
            st.write("Could not fetch jobs")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "🔄 Pipeline Progress", "📊 Results"])
    
    with tab1:
        st.markdown("## 📤 Upload and Analyze Images")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
            help="Upload an image to analyze for character sprite generation"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### 📷 Uploaded Image")
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                # Upload to API
                if st.button("📤 Upload to Server"):
                    with st.spinner("Uploading image..."):
                        upload_result = upload_image_to_api(uploaded_file)
                        if upload_result:
                            st.success("✅ Image uploaded successfully!")
                            st.session_state['uploaded_file_path'] = upload_result['file_path']
                            st.session_state['file_id'] = upload_result['file_id']
            
            with col2:
                st.markdown("### 🔍 Analysis")
                if st.button("🔍 Analyze Image") and 'uploaded_file_path' in st.session_state:
                    with st.spinner("Analyzing image..."):
                        analysis = analyze_image_with_api(st.session_state['uploaded_file_path'])
                        if analysis:
                            st.session_state['analysis'] = analysis
                            display_analysis_results(analysis)
                elif 'analysis' in st.session_state:
                    display_analysis_results(st.session_state['analysis'])
    
    with tab2:
        st.markdown("## 🔄 Pipeline Progress")
        
        # Start pipeline button
        if st.button("🚀 Start Pipeline", type="primary"):
            with st.spinner("Starting pipeline..."):
                pipeline_result = start_pipeline(
                    use_google_search=use_google_search,
                    character_name=character_name,
                    max_candidates=max_candidates
                )
                if pipeline_result:
                    st.session_state['current_job_id'] = pipeline_result['job_id']
                    st.success(f"✅ Pipeline started! Job ID: {pipeline_result['job_id']}")
        
        # Display progress if job is running
        if 'current_job_id' in st.session_state:
            job_id = st.session_state['current_job_id']
            
            # Auto-refresh every 2 seconds
            if st.button("🔄 Refresh Status"):
                st.rerun()
            
            # Get job status
            status = get_job_status(job_id)
            if status:
                # Display current status
                st.markdown(f"""
                <div class="step-card">
                    <h3>🔄 {status['current_step']}</h3>
                    <p>{status['message']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Progress bar
                display_progress_bar(status['progress'], status['current_step'], status['message'])
                
                # Status indicator
                if status['status'] == 'completed':
                    st.markdown('<p class="status-success">✅ Pipeline Completed!</p>', unsafe_allow_html=True)
                    st.session_state['pipeline_results'] = status['results']
                elif status['status'] == 'error':
                    st.markdown(f'<p class="status-error">❌ Error: {status["error"]}</p>', unsafe_allow_html=True)
                elif status['status'] == 'processing':
                    st.markdown('<p class="status-processing">🔄 Processing...</p>', unsafe_allow_html=True)
                    # Auto-refresh in 2 seconds
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Could not fetch job status")
    
    with tab3:
        st.markdown("## 📊 Results")
        
        if 'pipeline_results' in st.session_state:
            results = st.session_state['pipeline_results']
            
            st.markdown(f"### 🎯 Generated {results['total_sprites']} Character Sprites")
            
            # Display sprites
            for i, sprite in enumerate(results['sprites']):
                st.markdown(f"#### Sprite {i+1}")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if os.path.exists(sprite['path']):
                        img = Image.open(sprite['path'])
                        st.image(img, caption=f"Sprite {i+1}", use_column_width=True)
                
                with col2:
                    st.markdown(f"**Score:** {sprite['score']}/100")
                    st.markdown(f"**Status:** {'✅ READY' if sprite['score'] >= 60 else '⚠️ NEEDS REVIEW'}")
                    
                    # Show analysis
                    cowboy_analysis = sprite.get('cowboy_analysis', {})
                    st.markdown(f"**Analysis:** {cowboy_analysis.get('reason', 'Unknown')}")
                    
                    original_analysis = sprite.get('original_analysis', {})
                    if original_analysis.get('needs_outpainting'):
                        st.markdown(f"**Outpainting:** {original_analysis.get('reason', 'Unknown')}")
                        st.markdown(f"**Strategy:** {original_analysis.get('strategy', 'Unknown')}")
                    else:
                        st.markdown("**Outpainting:** Not needed")
            
            # Download button
            st.markdown("### 📥 Download Results")
            if st.button("📦 Download All Sprites"):
                # Create a zip file with all sprites
                import zipfile
                import io
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for i, sprite in enumerate(results['sprites']):
                        if os.path.exists(sprite['path']):
                            zip_file.write(sprite['path'], f"sprite_{i+1:02d}.jpg")
                
                zip_buffer.seek(0)
                st.download_button(
                    label="📥 Download ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"character_sprites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
        else:
            st.info("No results available. Run the pipeline first!")

if __name__ == "__main__":
    main()
