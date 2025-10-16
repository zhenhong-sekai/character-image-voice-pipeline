# 📁 Project Structure

## 🎯 Core Application Files
```
├── gradio_app.py                    # Main Gradio frontend application
├── api_server.py                   # FastAPI backend server
├── character_image_pipeline.py      # Core image processing pipeline
├── google_search_integration.py    # Google search functionality
├── main.py                         # Legacy main entry point
├── start_frontend.py               # Streamlit frontend
├── streamlit_app.py                # Streamlit application
├── launch_gradio.py                # Gradio launcher
├── requirements.txt                # Backend dependencies
├── requirements_frontend.txt       # Frontend dependencies
└── .env.example                   # Environment variables template
```

## 📂 Organized Folders

### 🧪 `tests/` - Test Files
- `test_api_key.py` - API key testing
- `test_auth_methods.py` - Authentication testing
- `test_google_images.py` - Google Images testing
- `test_google_search.py` - Google Search testing
- `test_lightx_simple.py` - LightX API testing
- `test_exact_query.py` - Query testing
- `lightx_outpainting_test.py` - LightX outpainting tests

### 📜 `scripts/` - Standalone Scripts
- `run_pipeline_with_search.py` - Pipeline with Google search
- `outpainting_decision_demo.py` - Outpainting decision demo
- `comfyui_outpainting.py` - ComfyUI outpainting script
- `launch_frontend.sh` - Frontend launcher
- `start_gradio.sh` - Gradio starter
- `start_gradio_simple.sh` - Simple Gradio starter

### ⚙️ `config/` - Configuration Files
- `workflow.json` - ComfyUI workflow
- `workflow2.json` - Alternative workflow
- `workflow3.json` - Third workflow
- `workflow4.json` - Fourth workflow
- `working.json` - Working workflow
- `flux-outpaint.json` - Flux outpainting config

### 📚 `docs/` - Documentation
- `README.md` - Main project documentation
- `FRONTEND_README.md` - Frontend documentation
- `FRONTEND_COMPARISON.md` - Frontend comparison
- `GOOGLE_SEARCH_README.md` - Google search docs
- `LIGHTX_README.md` - LightX API documentation

### 🎨 `examples/` - Example Files
- `outpainted_test.jpg` - Test outpainting result
- `output_*.png` - Various output examples
- `input.jpeg` - Test input image

### 🗃️ `archive/` - Archived Content
- `comfyui_debug.log` - Debug logs
- `Taylor swift_*/` - Archived Taylor Swift images
- Various archived image folders

### 🤖 `models/` - AI Models
- `yolov8n.pt` - YOLO face detection model

### 🎤 `voice/` - Voice Processing
- `main.py` - Voice pipeline main script
- `audio_segments_*/` - Extracted audio segments
- `transcript_*.txt` - Generated transcripts
- `mp4_files/` - Processed video files

## 🚫 Excluded from Git
- `uploaded_images/` - User uploaded images
- `character_sprites/` - Generated sprites
- `voice/audio_segments_*/` - Generated audio segments
- `downloaded_images/` - Downloaded images
- `.env` - Environment variables (contains API keys)
- `__pycache__/` - Python cache files
