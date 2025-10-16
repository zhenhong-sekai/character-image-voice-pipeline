# Test Files

This folder contains granular test files for different components of the Character Image Acquisition Pipeline.

## Test Files

### **Core API Tests**
- **`test_lightx_simple.py`** - Test LightX outpainting API with a simple image
- **`test_google_search.py`** - Test Google Custom Search API connectivity
- **`test_google_images.py`** - Test Google image search and download functionality

### **API Debugging Tests**
- **`test_api_key.py`** - Test different Google API endpoints
- **`test_auth_methods.py`** - Test different authentication methods for LightX API
- **`lightx_outpainting_test.py`** - Comprehensive LightX outpainting workflow test

## How to Use

### **Test Google Search API**
```bash
python3 tests/test_google_search.py
```

### **Test Google Image Download**
```bash
python3 tests/test_google_images.py
```

### **Test LightX Outpainting**
```bash
python3 tests/test_lightx_simple.py
```

### **Test Complete LightX Workflow**
```bash
python3 tests/lightx_outpainting_test.py
```

## Notes

- These are development/debugging test files
- They help verify individual components work correctly
- Use them to troubleshoot specific API issues
- The main pipeline (`character_image_pipeline.py`) integrates all these components

