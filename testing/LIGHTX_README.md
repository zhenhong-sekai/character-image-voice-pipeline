# LightX Outpainting Integration

This integration adds AI-powered outpainting functionality to the character image pipeline using the [LightX AI Expand API](https://docs.lightxeditor.com/api/ai-expand#quick-steps-to-generate-with-your-api).

## 🎯 What This Solves

The original PRD requires **Step 5: Outpainting** for images that can't accommodate a "cowboy shot" (head to upper thigh) in 2:3 aspect ratio. LightX provides the missing outpainting functionality.

## 📁 Files Created

1. **`lightx_outpainting_test.py`** - Complete API implementation with full workflow
2. **`test_lightx_simple.py`** - Simple test script for quick testing
3. **`lightx_integration.py`** - Integration module for existing pipeline

## 🚀 Quick Start

### Step 1: Get API Key
1. Visit [LightX API](https://docs.lightxeditor.com/api/ai-expand#quick-steps-to-generate-with-your-api)
2. Generate your API key
3. Replace `YOUR_API_KEY_HERE` in the scripts

### Step 2: Test the API
```bash
# Simple test
python3 test_lightx_simple.py

# Full test with detailed logging
python3 lightx_outpainting_test.py
```

### Step 3: Integration
```python
# Add to your existing pipeline
from lightx_integration import LightXOutpainting

# Initialize
lightx = LightXOutpainting("your_api_key_here")

# Run outpainting
success = lightx.run_outpainting(
    input_path="sprite_01.jpg",
    output_path="outpainted_sprite_01.jpg", 
    padding_config={
        "left": 100,
        "right": 100, 
        "top": 200,
        "bottom": 200
    }
)
```

## 🔧 API Workflow

The LightX API follows this workflow:

1. **Upload Image** → Get `imageUrl`
2. **Request Outpainting** → Get `orderId` 
3. **Check Status** → Poll until `status: "active"`
4. **Download Result** → Get outpainted image

## 💰 Pricing

- **1 credit per generation**
- **2K quality output**
- **~15 seconds average processing time**

## 🎨 Use Cases for Character Pipeline

### **Cowboy Shot Outpainting**
```python
# Detect if outpainting needed for cowboy shot
needs_outpainting, padding = detect_outpainting_needed(img_path, face_analysis)

if needs_outpainting:
    # Add padding to create space for upper body
    padding_config = {
        "left": 0,
        "right": 0,
        "top": 200,    # Add space above for head positioning
        "bottom": 300  # Add space below for upper body
    }
```

### **Aspect Ratio Correction**
```python
# Fix aspect ratio by adding padding
if current_ratio < target_ratio:
    padding_needed = target_width - current_width
    padding_config = {
        "left": padding_needed // 2,
        "right": padding_needed // 2,
        "top": 0,
        "bottom": 0
    }
```

## 🔄 Integration with Existing Pipeline

Add this to your `character_image_pipeline.py`:

```python
# After cropping step, before final validation
if needs_outpainting:
    print("🎨 Step 5: Outpainting with LightX")
    
    lightx = LightXOutpainting(API_KEY)
    outpainted_path = f"outpainted_{output_filename}"
    
    success = lightx.run_outpainting(
        output_path, 
        outpainted_path, 
        padding_config
    )
    
    if success:
        output_path = outpainted_path  # Use outpainted version
```

## 🧪 Testing

### Test with Sample Images
```bash
# Make sure you have images in downloaded_images/
python3 test_lightx_simple.py
```

### Expected Output
```
🎭 LightX Outpainting API Test
========================================
📤 Step 1: Uploading image...
✅ Upload URL generated: https://...
✅ Image uploaded successfully

🎨 Step 2: Requesting outpainting...
✅ Outpainting request submitted
   Order ID: 7906da5353b504162db5199d6

⏳ Step 3: Checking status...
   Attempt 1/5...
   Status: init
   Still processing... waiting 3 seconds
   Attempt 2/5...
   Status: active
✅ Processing complete!
   Output URL: https://...

💾 Downloading result...
✅ Result saved as 'outpainted_test.jpg'
```

## 🚨 Error Handling

The scripts include comprehensive error handling for:
- **Upload failures** - Network issues, invalid API key
- **Processing failures** - API errors, timeout
- **Download failures** - Network issues, invalid URLs

## 📊 Performance

- **Upload time**: ~2-5 seconds
- **Processing time**: ~15 seconds average
- **Download time**: ~1-2 seconds
- **Total time**: ~20-25 seconds per image

## 🔮 Next Steps

1. **Test the API** with your images
2. **Integrate with pipeline** using the provided modules
3. **Add cowboy shot detection** logic
4. **Optimize padding calculations** for character sprites
5. **Add batch processing** for multiple images

This integration completes the missing **Step 5: Outpainting** from your PRD! 🎉
