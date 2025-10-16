#!/usr/bin/env python3
"""
Test LightX API Key with different endpoints
"""

import os
import requests
import json

def test_api_key():
    API_KEY = os.getenv("LIGHTX_API_KEY", "your_lightx_api_key_here")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    print("🔑 Testing LightX API Key")
    print("=" * 30)
    
    # Test different endpoints
    endpoints = [
        "https://api.lightxeditor.com/external/api/v2/ai-expand",
        "https://api.lightxeditor.com/external/api/v1/ai-expand", 
        "https://api.lightxeditor.com/external/api/v2/ai-expand-photo",
        "https://api.lightxeditor.com/external/api/v1/ai-expand-photo"
    ]
    
    test_data = {
        "imageUrl": "https://example.com/test.jpg",
        "leftPadding": 0,
        "rightPadding": 0,
        "topPadding": 0,
        "bottomPadding": 0
    }
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing endpoint: {endpoint}")
        try:
            response = requests.post(endpoint, headers=headers, json=test_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_api_key()
