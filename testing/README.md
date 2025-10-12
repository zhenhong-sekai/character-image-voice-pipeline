# Character Image Acquisition Pipeline

Complete implementation of the PRD for Sekai character sprite generation with AI-powered outpainting and Google Custom Search integration.

## 🎯 Features

- **Google Custom Search API** - Automatic image search and download
- **LightX Outpainting API** - AI-powered image expansion for cowboy shots
- **YOLO Face Detection** - Person and face detection with positioning analysis
- **Smart Cropping** - Automatic 2:3 aspect ratio (1024x1536) conversion
- **Quality Validation** - Face positioning and dimension validation
- **Character Sprite Generation** - Ready-to-use game sprites

## 🚀 Quick Start

### **Option 1: Search and Process Images**
```bash
python3 run_pipeline_with_search.py
```
Edit the `character_name` in the script to search for any character.

### **Option 2: Process Existing Images**
```bash
python3 character_image_pipeline.py
```
Processes images already in the `downloaded_images/` folder.

### **Option 3: Direct Function Call**
```python
from character_image_pipeline import process_character_pipeline
process_character_pipeline(character_name="anime character", use_google_search=True)
```

## 📁 Project Structure

```
├── character_image_pipeline.py      # Main pipeline script
├── google_search_integration.py     # Google Custom Search API
├── run_pipeline_with_search.py      # Simple runner script
├── tests/                           # Test files
│   ├── test_google_search.py       # Google API test
│   ├── test_google_images.py       # Image download test
│   ├── test_lightx_simple.py       # LightX API test
│   └── README.md                    # Test documentation
├── downloaded_images/               # Input images folder
├── character_sprites/               # Output sprites folder
└── README.md                       # This file
```

## 🔑 API Keys Required

### **Google Custom Search API**
- **API Key**: Set in `google_search_integration.py`
- **Search Engine ID**: Set in `google_search_integration.py`
- **Setup**: See `GOOGLE_SEARCH_README.md`

### **LightX Outpainting API**
- **API Key**: Set in `character_image_pipeline.py`
- **Setup**: See `LIGHTX_README.md`

## 📊 Pipeline Steps

1. **Image Acquisition** - Google Custom Search or local folder
2. **Image Validation** - Face detection and quality checks
3. **Face Detection & Positioning** - YOLO-based analysis
4. **Aspect Ratio & Cropping** - 2:3 ratio conversion (1024x1536)
5. **Outpainting** - AI expansion for cowboy shots (if needed)
6. **Final Validation** - Quality and dimension checks

## 🎭 Output

- **Format**: 1024x1536 JPEG images
- **Location**: `character_sprites/` folder
- **Naming**: `sprite_01.jpg`, `sprite_02.jpg`, etc.
- **Quality**: Face positioning analysis and recommendations

## 🧪 Testing

Individual component tests are available in the `tests/` folder:

```bash
# Test Google Search API
python3 tests/test_google_search.py

# Test Google Image Download
python3 tests/test_google_images.py

# Test LightX Outpainting
python3 tests/test_lightx_simple.py
```

## 📚 Documentation

- **`GOOGLE_SEARCH_README.md`** - Google Custom Search API setup
- **`LIGHTX_README.md`** - LightX outpainting API setup
- **`tests/README.md`** - Test files documentation

## 🎯 Use Cases

- **Game Development** - Character sprite generation
- **Content Creation** - Character image processing
- **AI Art** - Automated character image enhancement
- **Research** - Image processing and AI integration

## 🔧 Configuration

Edit the configuration variables in `character_image_pipeline.py`:

```python
# LightX API Configuration
LIGHTX_API_KEY = "your_lightx_api_key_here"

# Target dimensions
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1536
```

## 📈 Performance

- **Google Search**: ~3-5 seconds per query
- **LightX Outpainting**: ~20-30 seconds per image
- **Face Detection**: ~1-2 seconds per image
- **Total Pipeline**: ~2-5 minutes for 10 images

## 🎉 Success!

The pipeline successfully generates character sprites with:
- ✅ Automatic image search and download
- ✅ AI-powered outpainting for cowboy shots
- ✅ Smart face detection and positioning
- ✅ Professional 1024x1536 output format
- ✅ Quality validation and recommendations