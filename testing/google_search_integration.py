#!/usr/bin/env python3
"""
Google Custom Search API Integration for Character Image Acquisition Pipeline
"""

import requests
import os
import time
from urllib.parse import quote
import json

# Google Custom Search API Configuration
GOOGLE_API_KEY = "AIzaSyBdXRfCxg04ukpG62qkP7GHYNxtnALljok"  # Your Google API key
GOOGLE_SEARCH_ENGINE_ID = "b0892825015e645e6"  # Your Search Engine ID (sekai_test)

def search_google_images(query, num_results=10, img_size="large", img_type="photo"):
    """
    Search for images using Google Custom Search API
    
    Args:
        query: Search query string
        num_results: Number of results to return (max 10 per request)
        img_size: Image size filter (small, medium, large, xlarge, xxlarge, huge)
        img_type: Image type filter (photo, clipart, lineart, face, animated)
    
    Returns:
        List of image URLs and metadata
    """
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        print("❌ Google API key not configured")
        return []
    
    if not GOOGLE_SEARCH_ENGINE_ID or GOOGLE_SEARCH_ENGINE_ID == "YOUR_SEARCH_ENGINE_ID_HERE":
        print("❌ Google Search Engine ID not configured")
        return []
    
    print(f"🔍 Searching Google Images for: '{query}'")
    
    # Google Custom Search API endpoint
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    # API parameters
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_SEARCH_ENGINE_ID,
        'q': query,
        'searchType': 'image',
        'num': min(num_results, 10),  # Max 10 per request
        'imgSize': img_size,
        'imgType': img_type,
        'safe': 'medium',  # Safe search filter
        'fileType': 'jpg,png,jpeg',  # Image file types
        'rights': 'cc_publicdomain,cc_attribute,cc_sharealike,cc_noncommercial,cc_nonderived'  # Usage rights
    }
    
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                results = []
                for item in data['items']:
                    result = {
                        'url': item.get('link', ''),
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'image_url': item.get('image', {}).get('contextLink', ''),
                        'thumbnail': item.get('image', {}).get('thumbnailLink', ''),
                        'width': item.get('image', {}).get('width', 0),
                        'height': item.get('image', {}).get('height', 0),
                        'file_size': item.get('image', {}).get('byteSize', 0)
                    }
                    results.append(result)
                
                print(f"✅ Found {len(results)} images")
                return results
            else:
                print("❌ No images found")
                return []
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def download_image(url, filename, download_dir="downloaded_images"):
    """
    Download an image from URL
    
    Args:
        url: Image URL
        filename: Local filename to save as
        download_dir: Directory to save the image
    
    Returns:
        Path to downloaded image or None if failed
    """
    try:
        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Download the image
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Determine file extension from content type
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'  # Default
            
            # Create full path
            filepath = os.path.join(download_dir, f"{filename}{ext}")
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✅ Downloaded: {os.path.basename(filepath)}")
            return filepath
        else:
            print(f"  ❌ Download failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None

def search_and_download_images(character_name, num_images=10, download_dir="downloaded_images"):
    """
    Search for character images and download them using exact query
    
    Args:
        character_name: Name of the character to search for (exact query)
        num_images: Number of images to download
        download_dir: Directory to save images
    
    Returns:
        List of downloaded image paths
    """
    print(f"🎭 Searching for images of: {character_name}")
    print("=" * 50)
    
    # Use exact query without appending extra words
    print(f"\n🔍 Query: {character_name}")
    results = search_google_images(character_name, num_results=num_images, img_size="large", img_type="photo")
    
    if not results:
        print("❌ No images found")
        return []
    
    print(f"\n📊 Found {len(results)} images")
    
    # Download images
    downloaded_images = []
    for i, result in enumerate(results[:num_images]):
        print(f"\n📥 Downloading image {i+1}/{min(num_images, len(results))}")
        print(f"  Title: {result['title'][:50]}...")
        print(f"  Size: {result['width']}x{result['height']}")
        
        # Create filename from title
        safe_title = "".join(c for c in result['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:30]  # Limit length
        filename = f"{character_name}_{i+1:02d}_{safe_title}"
        
        # Download the image
        filepath = download_image(result['url'], filename, download_dir)
        if filepath:
            downloaded_images.append(filepath)
        
        # Add delay between downloads
        time.sleep(0.5)
    
    print(f"\n✅ Successfully downloaded {len(downloaded_images)} images")
    return downloaded_images

def test_google_search():
    """Test the Google Custom Search API"""
    print("🧪 Testing Google Custom Search API")
    print("=" * 40)
    
    # Test search
    results = search_google_images("anime character portrait", num_results=3)
    
    if results:
        print(f"✅ API working! Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['title'][:50]}...")
            print(f"     URL: {result['url'][:60]}...")
            print(f"     Size: {result['width']}x{result['height']}")
    else:
        print("❌ API test failed")
        print("\n🔧 Setup Instructions:")
        print("1. Get Google API Key from: https://console.cloud.google.com/")
        print("2. Get Search Engine ID from: https://programmablesearchengine.google.com/")
        print("3. Update GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID in this file")

if __name__ == "__main__":
    test_google_search()
