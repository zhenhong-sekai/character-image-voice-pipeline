#!/usr/bin/env python3
"""
Test Google Search Image Download
Simple script to test downloading images from Google Custom Search API
"""

from google_search_integration import search_google_images, download_image
import os

def main():
    print("🔍 Testing Google Search Image Download")
    print("=" * 50)
    
    # Test parameters - you can modify these
    query = "donald trump"  # Exact query without extra words
    num_images = 5
    
    print(f"Searching for: {query}")
    print(f"Number of images: {num_images}")
    print()
    
    # Search for images using exact query
    results = search_google_images(query, num_results=num_images)
    
    if not results:
        print("❌ No images found")
        return
    
    print(f"Found {len(results)} images")
    
    # Download images
    downloaded_images = []
    for i, result in enumerate(results[:num_images]):
        print(f"\n📥 Downloading image {i+1}/{min(num_images, len(results))}")
        print(f"  Title: {result['title'][:50]}...")
        print(f"  Size: {result['width']}x{result['height']}")
        
        # Create filename
        safe_title = "".join(c for c in result['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:30]
        filename = f"exact_{i+1:02d}_{safe_title}"
        
        # Download the image
        filepath = download_image(result['url'], filename, "downloaded_images")
        if filepath:
            downloaded_images.append(filepath)
    
    if downloaded_images:
        print(f"\n✅ Successfully downloaded {len(downloaded_images)} images:")
        for i, image_path in enumerate(downloaded_images, 1):
            print(f"  {i}. {image_path}")
    else:
        print("\n❌ No images were downloaded")

if __name__ == "__main__":
    main()
