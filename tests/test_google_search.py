#!/usr/bin/env python3
"""
Test Google Custom Search API Integration
"""

from google_search_integration import test_google_search, search_and_download_images

def main():
    print("🧪 Google Custom Search API Test")
    print("=" * 40)
    
    # Test the API
    test_google_search()
    
    print("\n" + "=" * 40)
    print("📋 Setup Instructions:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable 'Custom Search API' in the Library section")
    print("4. Create an API key in the Credentials section")
    print("5. Go to https://programmablesearchengine.google.com/")
    print("6. Create a new search engine")
    print("7. Update the API keys in google_search_integration.py")
    print("\n🔑 Required Keys:")
    print("- GOOGLE_API_KEY: Your Google API key")
    print("- GOOGLE_SEARCH_ENGINE_ID: Your Search Engine ID (cx)")

if __name__ == "__main__":
    main()
