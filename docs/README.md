# Character Image Voice Acquisition Project

A complete pipeline for acquiring, processing, and generating character sprites using ComfyUI outpainting.

## 🎯 Project Overview

This project provides a comprehensive solution for:
- **Google Image Search** - Automatically finding character images
- **Image Validation** - Quality checks and face detection
- **ComfyUI Outpainting** - AI-powered image extension using Flux models
- **Character Sprite Generation** - Creating game-ready character sprites

## 📁 Project Structure

```
character_image_voice_acquisition/
├── main.py                          # ComfyUI API test script
├── character_image_pipeline.py       # Main pipeline with ComfyUI integration
├── comfyui_outpainting.py           # ComfyUI outpainting module
├── run_pipeline_with_search.py      # Pipeline runner with Google search
├── google_search_integration.py     # Google image search functionality
├── working.json                     # ComfyUI outpainting workflow
├── workflow.json                    # Simple ComfyUI workflow
├── flux-outpaint.json              # Flux outpainting workflow
├── models/yolov8n.pt                # YOLO model for face detection
├── input.jpeg                       # Test input image
├── downloaded_images/               # Downloaded character images
├── character_sprites/               # Generated character sprites
└── tests/                          # Test files
```

## 🚀 Quick Start

### 1. Run the Complete Pipeline
```bash
python3 run_pipeline_with_search.py
```

### 2. Test ComfyUI Integration
```bash
python3 main.py
```

### 3. Run Pipeline on Existing Images
```bash
python3 character_image_pipeline.py
```

## 🔧 Key Features

### ✅ **ComfyUI Integration**
- **ETN_LoadImageBase64** - Direct base64 image input
- **Flux Outpainting** - High-quality image extension
- **Random Seed Generation** - Prevents caching issues
- **Automatic Image Retrieval** - Downloads results automatically

### ✅ **Image Processing Pipeline**
- **Google Image Search** - Automatic character image discovery
- **YOLO Face Detection** - Quality validation and face positioning
- **Smart Cropping** - Automatic aspect ratio correction
- **Intelligent Outpainting** - Only when needed for cowboy shots

### ✅ **Character Sprite Generation**
- **1024x1536 Resolution** - Game-ready sprite dimensions
- **Quality Validation** - Face positioning and size checks
- **Batch Processing** - Multiple images at once
- **Output Organization** - Clean sprite generation

## 🎨 ComfyUI Workflows

### **working.json** - Main Outpainting Workflow
- Uses `ETN_LoadImageBase64` for direct image input
- Flux model for high-quality outpainting
- Configurable padding (left, right, top, bottom)
- Text prompt integration for guided outpainting

### **workflow.json** - Simple Generation Workflow
- Basic image generation workflow
- VAE encoding/decoding
- CLIP text encoding
- KSampler for generation

## 📊 Pipeline Steps

1. **🔍 Image Search** - Find character images via Google
2. **📥 Download** - Save images to `downloaded_images/`
3. **🔍 Validation** - Quality checks and face detection
4. **✂️ Cropping** - Resize to target dimensions (1024x1536)
5. **🎨 Outpainting** - Extend images using ComfyUI when needed
6. **✅ Final Validation** - Quality checks on final sprites
7. **💾 Output** - Save to `character_sprites/`

## 🛠️ Configuration

### ComfyUI Server
```python
HTTP_SERVER = "http://18.189.25.28:8004"
WS_SERVER = "ws://18.189.25.28:8004/ws"
```

### Target Dimensions
```python
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1536
TARGET_ASPECT_RATIO = 2/3  # Portrait format
```

## 📈 Results

The pipeline successfully:
- ✅ **Replaced LightX with ComfyUI** - No API costs, better quality
- ✅ **Integrated Google Search** - Automatic image discovery
- ✅ **Implemented Smart Validation** - Quality and face detection
- ✅ **Created Character Sprites** - Game-ready output images

## 🎯 Usage Examples

### Search and Process Donald Trump Images
```bash
python3 run_pipeline_with_search.py
```

### Process Existing Images
```bash
# Add images to downloaded_images/ folder first
python3 character_image_pipeline.py
```

### Test ComfyUI API
```bash
python3 main.py
```

## 🔧 Dependencies

- **ComfyUI Server** - Running on 18.189.25.28:8004
- **Python Libraries** - requests, websocket, cv2, PIL, ultralytics
- **YOLO Model** - models/yolov8n.pt for face detection
- **ComfyUI Workflows** - working.json, workflow.json

## 📝 Notes

- **No API Keys Required** - ComfyUI runs locally
- **Cost-Free Processing** - No external API costs
- **High Quality Output** - Flux model for professional results
- **Automatic Organization** - Clean file structure and naming

---

**🎭 Character Image Voice Acquisition Project** - Complete pipeline for character sprite generation with ComfyUI outpainting integration.