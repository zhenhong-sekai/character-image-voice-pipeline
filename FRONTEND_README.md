# 🎭 Character Image Pipeline Frontend

A beautiful Streamlit frontend with real-time progress tracking for the Character Image Pipeline.

## 🚀 Quick Start

### Option 1: Simple Launch
```bash
./launch_frontend.sh
```

### Option 2: Manual Launch
```bash
# Install requirements
pip install -r requirements_frontend.txt

# Start API server (in one terminal)
python api_server.py

# Start Streamlit app (in another terminal)
streamlit run streamlit_app.py
```

## 🌟 Features

### 📤 Upload & Analyze
- **Image Upload**: Drag & drop or click to upload images
- **Real-time Analysis**: Instant analysis of image quality, faces, and composition
- **Smart Detection**: YOLO-based face and body part detection
- **Cowboy Shot Analysis**: Intelligent detection of headshots vs cowboy shots

### 🔄 Pipeline Progress
- **Real-time Progress**: Live progress bars and step-by-step updates
- **Job Management**: Track multiple pipeline jobs
- **Status Updates**: Detailed status messages for each step
- **Auto-refresh**: Automatic progress updates every 2 seconds

### 📊 Results
- **Sprite Gallery**: View all generated character sprites
- **Quality Scores**: Smart scoring system (60-100 points)
- **Analysis Details**: Detailed breakdown of outpainting decisions
- **Download**: Download individual sprites or complete ZIP package

## 🎯 Pipeline Steps

1. **📁 Image Loading**: Scan for uploaded images
2. **🔍 Analysis**: Quality check, face detection, composition analysis
3. **🎨 Smart Outpainting**: AI-powered body extension for headshots
4. **✂️ Cropping**: Resize to target 1024x1536 dimensions
5. **✅ Validation**: Final quality check and scoring

## 🎨 Smart Outpainting Logic

The frontend shows real-time analysis of:

- **Face Position**: Where the face is located (top/middle/bottom)
- **Face Size**: How much of the image the face occupies
- **Composition**: Headshot vs partial body vs cowboy shot
- **Strategy**: Downward extension, upward extension, or no outpainting needed

## 🔧 API Endpoints

The frontend connects to a FastAPI backend with these endpoints:

- `POST /upload` - Upload images
- `POST /analyze` - Analyze single image
- `POST /process` - Start full pipeline
- `GET /status/{job_id}` - Get job progress
- `GET /jobs` - List all jobs

## 📱 UI Components

### Progress Tracking
- **Step Cards**: Beautiful gradient cards showing current step
- **Progress Bars**: Real-time progress indicators
- **Status Indicators**: Color-coded status (processing/success/error)

### Image Display
- **Upload Preview**: Instant image preview after upload
- **Analysis Results**: Detailed breakdown of image analysis
- **Sprite Gallery**: Grid view of generated sprites

### Controls
- **Pipeline Settings**: Google search, character name, max candidates
- **Job Management**: Start/stop/refresh pipeline jobs
- **Download Options**: Individual or bulk download

## 🎨 Styling

The frontend uses custom CSS for:
- **Gradient Headers**: Beautiful gradient text effects
- **Step Cards**: Gradient background cards for progress steps
- **Status Colors**: Green (success), Orange (processing), Red (error)
- **Responsive Layout**: Works on desktop and mobile

## 🔄 Real-time Updates

The frontend automatically:
- **Refreshes progress** every 2 seconds during processing
- **Updates status** when jobs complete or fail
- **Shows results** immediately when pipeline finishes
- **Manages jobs** with start/stop/delete functionality

## 📦 Installation

```bash
# Install all requirements
pip install -r requirements.txt
pip install -r requirements_frontend.txt

# Start the complete system
python start_frontend.py
```

## 🌐 Access

- **Streamlit App**: http://localhost:8501
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎭 Usage

1. **Upload Images**: Use the upload tab to add images
2. **Analyze**: Click "Analyze Image" to see detailed analysis
3. **Start Pipeline**: Go to "Pipeline Progress" and click "Start Pipeline"
4. **Monitor Progress**: Watch real-time progress updates
5. **View Results**: Check the "Results" tab for generated sprites
6. **Download**: Download individual sprites or complete package

The frontend provides a complete, user-friendly interface for the Character Image Pipeline with real-time progress tracking and beautiful visualizations! 🎨✨
