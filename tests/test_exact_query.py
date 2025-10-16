#!/usr/bin/env python3
"""
Test Google Search with Exact Query (No Appending)
"""

from google_search_integration import search_and_download_images

def main():
    print("🔍 Testing Google Search with Exact Query")
    print("=" * 50)
    
    # Test with exact query - no extra words will be added
    query = "anime character"  # This will be used exactly as-is
    num_images = 10
    
    print(f"Query: '{query}' (exact, no appending)")
    print(f"Number of images: {num_images}")
    print()
    
    # Search and download images using exact query
    downloaded_images = search_and_download_images(query, num_images)
    
    if downloaded_images:
        print(f"\n✅ Successfully downloaded {len(downloaded_images)} images:")
        for i, image_path in enumerate(downloaded_images, 1):
            print(f"  {i}. {image_path}")
    else:
        print("\n❌ No images were downloaded")

if __name__ == "__main__":
    main()

