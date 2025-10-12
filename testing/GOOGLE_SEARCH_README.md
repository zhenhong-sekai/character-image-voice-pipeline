# Google Custom Search API Integration

This document explains how to set up and use the Google Custom Search API for image search in the Character Image Acquisition Pipeline.

## 🔑 Required API Keys

You need **TWO** keys to use the Google Custom Search API:

1. **Google API Key** - For authentication
2. **Search Engine ID (cx)** - For the custom search engine

## 📋 Setup Instructions

### Step 1: Get Google API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **"APIs & Services" > "Library"**
4. Search for **"Custom Search API"** and enable it
5. Go to **"APIs & Services" > "Credentials"**
6. Click **"Create Credentials" > "API Key"**
7. Copy and save your API key

### Step 2: Create Custom Search Engine

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/all)
2. Click **"Add"** to create a new search engine
3. In **"Sites to search"**, enter:
   - `*` (to search the entire web)
   - Or specific sites like `pinterest.com`, `deviantart.com`, etc.
4. Give your search engine a name
5. Click **"Create"**
6. Copy the **Search Engine ID** (starts with a long string of characters)

### Step 3: Configure the Pipeline

Update the API keys in `google_search_integration.py`:

```python
# Replace these with your actual keys
GOOGLE_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
GOOGLE_SEARCH_ENGINE_ID = "YOUR_ACTUAL_SEARCH_ENGINE_ID_HERE"
```

## 🚀 Usage

### Test the API

```bash
python3 test_google_search.py
```

### Use in Pipeline

```python
# Search for images and process them
from character_image_pipeline import process_character_pipeline

# Search for "anime character" images and process them
process_character_pipeline(
    character_name="anime character", 
    use_google_search=True
)
```

### Direct Search

```python
from google_search_integration import search_and_download_images

# Search and download images
images = search_and_download_images("anime character", num_images=10)
print(f"Downloaded {len(images)} images")
```

## 🔧 API Parameters

The search function supports various parameters:

- **query**: Search term
- **num_results**: Number of results (max 10 per request)
- **img_size**: Image size filter (`small`, `medium`, `large`, `xlarge`, `xxlarge`, `huge`)
- **img_type**: Image type filter (`photo`, `clipart`, `lineart`, `face`, `animated`)

## 📊 Quota Limits

- **Free tier**: 100 queries per day
- **Paid tier**: Higher limits available
- **Rate limiting**: 1 second delay between requests

## 🛠️ Troubleshooting

### Common Issues

1. **"API key not valid"**
   - Check if the API key is correct
   - Ensure Custom Search API is enabled

2. **"Search Engine ID not found"**
   - Verify the Search Engine ID is correct
   - Check if the search engine is active

3. **"Quota exceeded"**
   - You've reached the daily limit
   - Wait 24 hours or upgrade to paid tier

4. **"No results found"**
   - Try different search terms
   - Check if the search engine is configured correctly

### Debug Mode

Enable debug mode to see detailed API responses:

```python
# In google_search_integration.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Example Usage

```python
# Search for anime character images
results = search_google_images(
    query="anime character portrait",
    num_results=5,
    img_size="large",
    img_type="photo"
)

# Download images
for i, result in enumerate(results):
    print(f"Image {i+1}: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Size: {result['width']}x{result['height']}")
```

## 🔒 Security Notes

- Keep your API keys secure
- Don't commit API keys to version control
- Consider using environment variables for production
- Monitor your API usage to avoid unexpected charges

## 📚 Additional Resources

- [Google Custom Search API Documentation](https://developers.google.com/custom-search/v1/using_rest)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
